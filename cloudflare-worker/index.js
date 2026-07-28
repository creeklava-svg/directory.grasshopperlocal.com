// directory.grasshopperlocal.com — Lead Capture & Routing Worker
// Deployed to iowa-directory-leads.workers.dev (Option B)
// Secrets set via `wrangler secret put <NAME>`

addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request))
})

async function handleRequest(request) {
  const url = new URL(request.url)
  const method = request.method

  // Handle lead form submissions (from the static site)
  if (url.pathname === '/api/lead' && method === 'POST') {
    return handleLead(request)
  }

  // Handle claim listing submissions
  if (url.pathname === '/api/claim' && method === 'POST') {
    return handleClaim(request)
  }

  // Stats endpoint — called by the weekly Telegram cron
  if (url.pathname === '/api/stats' && method === 'GET') {
    return handleStats(request)
  }

  // CORS preflight
  if (method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders() })
  }

  return new Response('Not found', { status: 404 })
}

// ─── LEAD HANDLING ─────────────────────────────────────────

async function handleLead(request) {
  const formData = await request.formData()
  const lead = {
    name: formData.get('name') || '',
    phone: formData.get('phone') || '',
    city: formData.get('city') || '',
    category: formData.get('category') || '',
    description: formData.get('description') || '',
    timestamp: new Date().toISOString(),
    id: crypto.randomUUID()
  }

  if (!lead.name || !lead.phone || !lead.city || !lead.category) {
    return redirectWithMessage('Please fill in all required fields.', 'https://directory.grasshopperlocal.com/lead-capture.html')
  }

  // Store lead in KV with 24-hour TTL
  await LEAD_KV.put(lead.id, JSON.stringify(lead), { expirationTtl: 86400 })

  // Track stats
  await incrementStat('total_leads')
  await incrementStat(`leads_${lead.city}_${lead.category}`)

  // Check for subscriber in this city+category
  const subKey = `subscriber:${lead.city}:${lead.category}`
  const subscriber = await LEAD_KV.get(subKey)

  if (subscriber) {
    // Route lead to subscriber via SMS (Telnyx)
    await sendSMS(subscriber, lead)
    await incrementStat('leads_routed')
    return redirectWithMessage("You've been matched! A local pro will call you shortly.", 'https://directory.grasshopperlocal.com/')
  } else {
    // No subscriber — log it for admin
    await incrementStat('leads_unmatched')
    return redirectWithMessage("Thanks! We're finding the right pro for you. Expect a call soon.", 'https://directory.grasshopperlocal.com/')
  }
}

// ─── CLAIM LISTING ─────────────────────────────────────────

async function handleClaim(request) {
  const formData = await request.formData()
  const claim = {
    business: formData.get('business') || '',
    city: formData.get('city') || '',
    category: formData.get('category') || '',
    business_name: formData.get('business_name') || '',
    owner_name: formData.get('owner_name') || '',
    email: formData.get('email') || '',
    phone: formData.get('phone') || '',
    premium: formData.get('premium') || 'maybe',
    timestamp: new Date().toISOString(),
    id: crypto.randomUUID()
  }

  if (!claim.business_name || !claim.owner_name || !claim.email) {
    return redirectWithMessage('Please fill in all required fields.', 'https://directory.grasshopperlocal.com/claim-listing.html')
  }

  // Store claim in KV
  await LEAD_KV.put(`claim:${claim.id}`, JSON.stringify(claim))
  await incrementStat('total_claims')

  return redirectWithMessage("Your claim has been submitted! We'll review and get back to you within 24 hours.", 'https://directory.grasshopperlocal.com/')
}

// ─── STATS ENDPOINT (called by weekly Telegram cron) ─────

async function handleStats(request) {
  // Simple token check so randos can't read stats
  const auth = request.headers.get('Authorization')
  const expected = typeof STATS_TOKEN !== 'undefined' && STATS_TOKEN ? `Bearer ${STATS_TOKEN}` : null
  if (expected && auth !== expected) {
    return new Response('Unauthorized', { status: 401, headers: corsHeaders() })
  }

  const totalLeads = parseInt(await LEAD_KV.get('stat:total_leads') || '0')
  const leadsRouted = parseInt(await LEAD_KV.get('stat:leads_routed') || '0')
  const leadsUnmatched = parseInt(await LEAD_KV.get('stat:leads_unmatched') || '0')
  const totalClaims = parseInt(await LEAD_KV.get('stat:total_claims') || '0')
  const leadsSold = parseInt(await LEAD_KV.get('stat:leads_sold') || '0')
  const totalRevenue = parseInt(await LEAD_KV.get('stat:total_revenue') || '0')

  return new Response(JSON.stringify({
    totalLeads,
    leadsRouted,
    leadsUnmatched,
    totalClaims,
    leadsSold,
    totalRevenue,
    lastUpdated: new Date().toISOString()
  }), {
    headers: {
      'Content-Type': 'application/json',
      ...corsHeaders()
    }
  })
}

// ─── LEAD SOLD WEBHOOK (called by Stripe after payment) ──

async function handleLeadSold(request) {
  // Stripe webhook — payment confirmed
  // Future: called by Stripe webhook endpoint
  await incrementStat('leads_sold')
  // Revenue tracking happens client-side for now
  return new Response('OK')
}

// ─── TELNYX SMS ────────────────────────────────────────────

async function sendSMS(toPhone, lead) {
  const TELNYX_API_KEY = TELNYX_API_KEY
  const TELNYX_PHONE = TELNYX_PHONE

  if (!TELNYX_API_KEY || !TELNYX_PHONE) {
    console.error('Telnyx not configured')
    return
  }

  const message = `NEW LEAD: ${lead.name} needs a ${lead.category} in ${lead.city}. Call ${lead.phone}. "${lead.description}"`

  try {
    const response = await fetch('https://api.telnyx.com/v2/messages', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${TELNYX_API_KEY}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        from: TELNYX_PHONE,
        to: toPhone,
        text: message
      })
    })
    if (!response.ok) {
      const err = await response.text()
      console.error('Telnyx send failed:', response.status, err)
    }
  } catch (e) {
    console.error('Telnyx send error:', e)
  }
}

// ─── HELPERS ───────────────────────────────────────────────

async function incrementStat(name) {
  try {
    const key = `stat:${name}`
    const val = parseInt(await LEAD_KV.get(key) || '0')
    await LEAD_KV.put(key, (val + 1).toString())
  } catch (e) {
    console.error('Stats increment failed:', e)
  }
}

function redirectWithMessage(message, path) {
  return Response.redirect(`${path}?msg=${encodeURIComponent(message)}`, 302)
}

function corsHeaders() {
  return {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization'
  }
}
