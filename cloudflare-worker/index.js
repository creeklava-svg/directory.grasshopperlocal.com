addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request))
})

async function handleRequest(request) {
  const url = new URL(request.url)

  // Handle lead form submissions
  if (url.pathname === '/api/lead' && request.method === 'POST') {
    return handleLead(request)
  }

  // Handle claim listing submissions
  if (url.pathname === '/api/claim' && request.method === 'POST') {
    return handleClaim(request)
  }

  // CORS preflight
  if (request.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders() })
  }

  return new Response('Not found', { status: 404 })
}

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
    return redirectWithMessage('Please fill in all required fields.', '/lead-capture.html')
  }

  // Store lead in KV with 24-hour TTL
  await LEAD_KV.put(lead.id, JSON.stringify(lead), { expirationTtl: 86400 })

  // Store in recent leads list
  const recentStr = await LEAD_KV.get('recent_leads', 'json') || []
  recentStr.unshift(lead.id)
  if (recentStr.length > 100) recentStr.pop()
  await LEAD_KV.put('recent_leads', JSON.stringify(recentStr))

  // Check for subscriber in this city+category
  const subKey = `subscriber:${lead.city}:${lead.category}`
  const subscriber = await LEAD_KV.get(subKey)

  if (subscriber) {
    // Route lead to subscriber via SMS (Twilio)
    await sendSMS(subscriber, lead)
    return redirectWithMessage('You\'ve been matched! A local pro will call you shortly.', '/')
  } else {
    // Hold lead — send email to top businesses
    await notifyBusinesses(lead)
    return redirectWithMessage('Thanks! We\'re finding the right pro for you. Expect a call soon.', '/')
  }
}

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
    return redirectWithMessage('Please fill in all required fields.', '/claim-listing.html')
  }

  // Store claim in KV
  await LEAD_KV.put(`claim:${claim.id}`, JSON.stringify(claim))

  // Add to pending claims list
  const pendingStr = await LEAD_KV.get('pending_claims', 'json') || []
  pendingStr.push(claim.id)
  await LEAD_KV.put('pending_claims', JSON.stringify(pendingStr))

  // Send notification email via SendGrid
  await sendEmail({
    to: 'help@grasshopperlocal.com',
    subject: `New claim listing: ${claim.business_name}`,
    text: `Business: ${claim.business_name}\nOwner: ${claim.owner_name}\nEmail: ${claim.email}\nPhone: ${claim.phone}\nPremium interest: ${claim.premium}\n\nClaim ID: ${claim.id}`
  })

  return redirectWithMessage('Your claim has been submitted! We\'ll review and get back to you within 24 hours.', '/')
}

async function sendSMS(phone, lead) {
  const TWILIO_ACCOUNT_SID = TWILIO_ACCOUNT_SID
  const TWILIO_AUTH_TOKEN = TWILIO_AUTH_TOKEN
  const TWILIO_PHONE = TWILIO_PHONE

  if (!TWILIO_ACCOUNT_SID || !TWILIO_AUTH_TOKEN) return

  const message = `NEW LEAD: ${lead.name} needs a ${lead.category} in ${lead.city}. Call ${lead.phone}. "${lead.description}"`

  try {
    const url = `https://api.twilio.com/2010-04-01/Accounts/${TWILIO_ACCOUNT_SID}/Messages.json`
    const auth = btoa(`${TWILIO_ACCOUNT_SID}:${TWILIO_AUTH_TOKEN}`)
    await fetch(url, {
      method: 'POST',
      headers: {
        'Authorization': `Basic ${auth}`,
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      body: new URLSearchParams({
        To: phone,
        From: TWILIO_PHONE,
        Body: message
      })
    })
  } catch (e) {
    console.error('SMS send failed:', e)
  }
}

async function notifyBusinesses(lead) {
  // In Phase 1, email admin with lead details
  // Future: email top 3 businesses in that city+category
  await sendEmail({
    to: 'help@grasshopperlocal.com',
    subject: `New lead available: ${lead.category} in ${lead.city}`,
    text: `Name: ${lead.name}\nPhone: ${lead.phone}\nCity: ${lead.city}\nCategory: ${lead.category}\nDescription: ${lead.description}\n\nNo subscriber found for this area. Email top businesses to offer this lead.`
  })
}

async function sendEmail({ to, subject, text }) {
  const SENDGRID_API_KEY = SENDGRID_API_KEY
  if (!SENDGRID_API_KEY) return

  try {
    await fetch('https://api.sendgrid.com/v3/mail/send', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${SENDGRID_API_KEY}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        personalizations: [{ to: [{ email: to }] }],
        from: { email: 'help@grasshopperlocal.com', name: 'Grasshopper Directory' },
        subject: subject,
        content: [{ type: 'text/plain', value: text }]
      })
    })
  } catch (e) {
    console.error('Email send failed:', e)
  }
}

function redirectWithMessage(message, path) {
  return Response.redirect(`${path}?msg=${encodeURIComponent(message)}`, 302)
}

function corsHeaders() {
  return {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type'
  }
}
