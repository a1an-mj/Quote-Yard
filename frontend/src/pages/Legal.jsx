import { Link } from 'react-router-dom'
import Footer from '../components/Footer'
import PublicNav from '../components/PublicNav'

// Shown on both pages. Change the date whenever either page changes.
const UPDATED = '3 November 2026'
const OPERATOR = 'Rohith Biju'
const CONTACT = 'rohithbijurandom@gmail.com'

function Contact() {
  return <a className="qy-link" href={`mailto:${CONTACT}`}>{CONTACT}</a>
}

function LegalPage({ title, intro, children }) {
  return (
    <>
      <PublicNav />
      <main className="qy-wrap" style={{ paddingBlock: '40px 72px' }}>
        <article className="qy-legal">
          <p className="qy-label">Last updated {UPDATED}</p>
          <h1 className="qy-h1">{title}</h1>
          <p className="qy-body qy-legal__intro">{intro}</p>
          {children}
        </article>
      </main>
      <Footer />
    </>
  )
}

function Part({ title, children }) {
  return (
    <section className="qy-legal__part">
      <h2 className="qy-h2">{title}</h2>
      {children}
    </section>
  )
}

export function Privacy() {
  return (
    <LegalPage
      title="Privacy policy"
      intro="What Quote Yard keeps about you, why, and how to have it removed. In short: only what an account needs, no ads, no tracking, and nothing is sold."
    >
      <Part title="Who runs Quote Yard">
        <p>Quote Yard is a price comparison site for Kerala, run by {OPERATOR} in Kerala, India. For any question about your data, or to make a request or complaint, email <Contact />.</p>
      </Part>

      <Part title="What we keep">
        <h3 className="qy-h3">If you have a customer account</h3>
        <ul>
          <li>Your first name, your last name if you give it, and your email address.</li>
          <li>Your password, stored only in a scrambled form (a hash) that cannot be turned back into the password. Nobody, us included, can read it.</li>
          <li>The products you save and their lowest price when you saved them, and the price alerts you set.</li>
          <li>When you last logged in, and a record of each login so you stay signed in. Each login stops working after 14 days.</li>
          <li>One-time codes we email you to confirm your address or reset your password. They are also stored scrambled and expire soon after.</li>
        </ul>
        <h3 className="qy-h3">If you have a shop account</h3>
        <ul>
          <li>The shop's name, the owner's name, email, phone number, address, town, district and, if given, GST number.</li>
          <li>The offers the shop adds, and a record of changes to the shop's account.</li>
          <li>The shop's name, phone number, town and district are <strong>shown publicly</strong> next to its offers, with a map link made from its address, so customers can call or find the shop. The GST number is never shown.</li>
        </ul>
        <h3 className="qy-h3">If you send feedback</h3>
        <p>The feedback form's answers, and your name and email if you choose to give them, are emailed to the Quote Yard team. They are not stored on the site, and are used only to improve it and, if you asked, to reply.</p>
        <h3 className="qy-h3">What every visit sends</h3>
        <p>Like any website, our server receives your IP address and the page you ask for. We use them only to keep the site working and to slow down repeated login attempts. They are not linked to your account, and server logs are deleted automatically as they get old.</p>
      </Part>

      <Part title="What we don't do">
        <ul>
          <li>No adverts, no tracking or analytics tools, and no social media buttons.</li>
          <li>We never sell, rent or share your details for marketing.</li>
          <li>We never ask for payment details or your location. You buy on the store's own website, not here.</li>
        </ul>
      </Part>

      <Part title="Why we keep it">
        <p>To run your account, to show your saved items, and to email you sign-up codes, password resets and the price alerts you asked for. We use your details only for these. By creating an account you agree to this use, and you can withdraw that agreement at any time by deleting your account.</p>
      </Part>

      <Part title="Cookies and your device">
        <ul>
          <li><strong>One cookie</strong>, <code>qy_session</code>, keeps you logged in for up to 14 days. The site cannot work without it, and it is removed when you log out.</li>
          <li>Your browser also remembers your Light or Dark choice and your recent searches. These stay on your device and are never sent to us.</li>
        </ul>
      </Part>

      <Part title="Who else is involved">
        <ul>
          <li><strong>Google (Gmail)</strong> delivers the emails we send you, and the team's feedback inbox is a Gmail account, so those messages pass through Google's mail service.</li>
          <li>Everything else runs on our own server in Kerala, India. The site's fonts are served by us too, so visiting does not contact Google or anyone else.</li>
          <li>We would only hand over data if Indian law required it.</li>
        </ul>
      </Part>

      <Part title="How long we keep it">
        <p>As long as your account exists. When you delete it, your details, saved items and alerts are removed straight away. Copies in our backups disappear as old backups are replaced: we keep 14 days of daily backups and 6 monthly ones, so all copies are gone within about 6 months.</p>
      </Part>

      <Part title="Your rights">
        <p>Under India's Digital Personal Data Protection Act, 2023, you can:</p>
        <ul>
          <li><strong>Delete your account</strong> yourself at any time: log in, open <Link className="qy-link" to="/saved">Saved</Link> and use Delete my account at the bottom.</li>
          <li>Ask for a copy of what we hold about you, or for something to be corrected.</li>
          <li>Name someone who can act for you if you die or cannot act yourself.</li>
          <li>Complain to us if you think we got something wrong.</li>
        </ul>
        <p>Shop owners can ask us to close a shop account and remove its details. For any of these, email <Contact />. We reply within 30 days. If you are not happy with our reply, you can complain to the Data Protection Board of India.</p>
      </Part>

      <Part title="Keeping it safe">
        <p>Passwords and codes are only stored scrambled, logins expire, repeated login attempts are slowed down, and the site is served over an encrypted connection. No system is perfectly safe; if your data were ever exposed, we would tell you and the Data Protection Board as the law requires.</p>
      </Part>

      <Part title="Age">
        <p>Quote Yard is meant for people aged 18 or over.</p>
      </Part>

      <Part title="Changes">
        <p>If this policy changes, the date at the top changes too. If a change affects how we use your details, we will email account holders before it applies.</p>
      </Part>
    </LegalPage>
  )
}

export function Terms() {
  return (
    <LegalPage
      title="Terms of use"
      intro="The rules for using Quote Yard. By using the site or creating an account, you agree to them."
    >
      <Part title="What Quote Yard is">
        <p>Quote Yard shows the prices that Kerala stores list on their own websites (myG, Oxygen, Pittappillil and Nandilath G Mart), side by side. It is run by {OPERATOR}. We don't sell anything, and we are not part of, paid by or endorsed by any of these stores. Store and brand names belong to their owners.</p>
      </Part>

      <Part title="Prices can be out of date or wrong">
        <ul>
          <li>We read each store's public website about once a day, so a price or stock status may have changed since.</li>
          <li>A price can be read wrongly, or two listings can be matched wrongly, even though we try hard to avoid it.</li>
          <li><strong>Always check the price and details on the store's own page before you buy.</strong> The store's price is the one that counts.</li>
          <li>Delivery charges, offers, cashback and EMI terms are not included.</li>
        </ul>
      </Part>

      <Part title="Deals">
        <p>A deal is either a price lower than the product's lowest price in the 30 days before, or one store listing it clearly below the next store. Both come only from prices we recorded. They are never measured against an MRP, and they are not offers from us.</p>
      </Part>

      <Part title="Buying">
        <p>When you buy, you buy from the store, on its website, under its terms. Questions about orders, delivery, returns or warranty go to that store; we can't help with them.</p>
      </Part>

      <Part title="Local shop offers">
        <p>Shops can add offers that appear next to store prices. We check who a shop is before it can post, but the shop sets its own price and is responsible for it. Call the shop to confirm the price and stock before you go. Your dealings with a shop are between you and the shop.</p>
      </Part>

      <Part title="Your account">
        <ul>
          <li>Give your real email address and keep your password to yourself. You are responsible for what is done with your account.</li>
          <li>One account per person. Accounts are for people aged 18 or over.</li>
          <li>You can delete your account at any time from the Saved page.</li>
        </ul>
      </Part>

      <Part title="Fair use">
        <p>Please don't:</p>
        <ul>
          <li>copy our data in bulk, or use bots, scrapers or scripts on the site;</li>
          <li>try to break into, overload or get around the site's limits and protections;</li>
          <li>create accounts in someone else's name, or use the site for anything unlawful.</li>
        </ul>
        <p>We may suspend or close accounts that do.</p>
      </Part>

      <Part title="For shops">
        <p>Offers must be real, for products you actually have, at a price you will honour, and must follow Indian consumer law. We may remove any offer, or suspend a shop account, that is misleading or breaks these terms.</p>
      </Part>

      <Part title="The service">
        <p>Quote Yard is free. We may change, pause or stop it, or any part of it, at any time. We provide it as it is, without promises that it is complete, correct or always available. As far as the law allows, we are not responsible for losses from relying on a price shown here, from a store's or shop's actions, or from the site being unavailable.</p>
      </Part>

      <Part title="Law">
        <p>These terms are governed by the laws of India, and the courts in Kerala decide any dispute.</p>
      </Part>

      <Part title="Changes and contact">
        <p>If these terms change, the date at the top changes too. Questions: email <Contact />. How we handle your data is in the <Link className="qy-link" to="/privacy">privacy policy</Link>.</p>
      </Part>
    </LegalPage>
  )
}
