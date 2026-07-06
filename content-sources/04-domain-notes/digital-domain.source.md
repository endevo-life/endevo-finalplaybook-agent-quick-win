# Digital domain — deterministic questions (source)

Same tiered pattern. **New shapes to note vs. Financial/Physical:**
- Some steps carry **fillable text fields** (e.g. name of trusted person, date set
  up, Face ID vs fingerprint). These become form inputs the member fills in, and
  should be captured as `fields: [...]` on the relevant step.
- References an external **Digital Asset Inventory Worksheet (fillable PDF)** —
  drop that PDF into `../03-andrea-work-items/` or here; note it as an attachment.
- D1.1 (phone unlock / Legacy Contact) and D1.2/D1.3 (password manager) are the
  **"basic steps first"** anchors — see `basic-steps-first.template.md`.

---

## D1 — Phone access, password manager, email

### D1.1 If you died tomorrow, could your trusted person unlock your phone within 24 hours (passcode shared, biometric backup plan, or Legacy Contact set up)?

- **Yes, they have the passcode AND a Legacy Contact is set up** → *review*
  - Checklist: passcode current/unchanged? Legacy Contact active/correct? trusted person knows what to do if biometric fails? plan updated if you changed phones?
- **They have the passcode OR a Legacy Contact — not both** → *steps*
  1. Confirm your trusted person knows your current passcode. — fields: `trustedPersonName`, `reviewDate`
  2. Set up a Legacy Contact on your device. — fields: `legacyContactSetupDate`
  3. Add a biometric backup plan (Face ID or fingerprint) if appropriate. — fields: `biometricAddedDate`, `biometricType (Face ID | fingerprint)`
  4. Tell your trusted person exactly how each method works and when to use it.
- **No** → *steps*
  1. Share your current passcode with your trusted person and store it securely. — fields: `trustedPersonName`, `reviewDate`
  2. Set up a Legacy Contact. — fields: `legacyContactSetupDate`
  3. Add biometric access if your device supports it. — fields: `biometricAddedDate`, `biometricType`
  4. Write down unlock instructions and store them with your legal documents. — fields: `instructionsStoredWhere`
  5. Review your access plan whenever you change devices or security settings.

### D1.2 Do you use a password manager (1Password, Bitwarden, Dashlane, LastPass, Apple Keychain) to store your login credentials?

> Reference: Digital Asset Inventory Worksheet (fillable PDF) — attach to this domain.

- **Yes, I use one and most of my logins are in it** → *review*
  - Checklist: major accounts (email, banking, cloud) included? recovery codes + 2FA backups stored? master password written down securely? trusted person knows how to access vault?
- **I use one but only for some accounts** → *steps*
  1. Identify accounts not yet stored (email, banking, utilities, subscriptions).
  2. Add each login with updated passwords and enable 2FA where possible.
  3. Store recovery codes and backup methods in the manager.
  4. Make sure your master password is written down securely and accessible to your trusted person if needed.
- **No** → *steps*
  1. Choose a password manager.
  2. Add your most important accounts first (email, banking, cloud storage).
  3. Enable 2FA and store recovery codes in the manager.
  4. Write down your master password and store it securely.
  5. Tell your trusted person how to access your vault if needed.

### D1.3 If you died tomorrow, would your trusted person be able to access your password manager (emergency access set up, master password shared securely, or instructions documented)?

- **Yes, emergency access is set up or master password is securely accessible** → *review*
  - Checklist: emergency access active/assigned? master password stored securely + current? trusted person knows where instructions are? new accounts/recovery codes added recently?
- **They know I use one but they do not have a way in** → *steps*
  1. Set up emergency access (or designate a Legacy Contact if supported).
  2. Write down your master password and store it securely (fireproof safe, sealed envelope, attorney's file).
  3. Document simple instructions for unlocking your vault.
  4. Tell your trusted person where the access information is stored.
- **No / I do not use a password manager** → *steps*
  1. Choose a password manager.
  2. Add your most important accounts first.
  3. Set up emergency access or document your master password securely.
  4. Write down instructions for accessing your vault.
  5. Tell your trusted person where the information is stored.

### D1.4 Have you documented every email account you use (personal, work, secondary, recovery) and how your trusted person can access them?

- **Yes, all email accounts documented with access instructions** → *review*
  - Checklist: all personal/work/recovery accounts listed? access instructions current? 2FA methods + recovery codes included? trusted person knows where documentation is stored?
- **Some accounts documented or no access instructions** → *steps*
  1. List every email account (personal, work, secondary, recovery).
  2. Add access instructions per account (password manager location, recovery codes, 2FA steps).
  3. Store the list securely with your digital-access plan or password manager.
  4. Tell your trusted person where the list is and how to use it.
  5. Update the list whenever you add or close an account.
- **No** → *steps*
  1. Identify every email account (personal, work, recovery, old accounts tied to services).
  2. Write down each account with access instructions.
  3. Store passwords and recovery codes in a password manager.
  4. Tell your trusted person where to find email-access instructions.
  5. Review your list annually.

---

## D2 — Social media, backups, digital assets, digital asset manager

### D2.1 Have you documented every social media account you have (Facebook, Instagram, LinkedIn, X, TikTok, YouTube, Snapchat, Reddit, etc.) and decided what happens to each one (memorialize, delete, transfer)?

- **Yes, all accounts listed and decisions documented** → *review*
  - Checklist: all accounts active/listed? memorialization/deletion instructions still right? login details in password manager? trusted person knows where documentation is kept?
- **Some accounts listed or no decisions made yet** → *steps*
  1. List every social-media account, including older/rarely used ones.
  2. Decide what should happen to each (memorialize, delete, transfer, archive).
  3. Add access instructions or note where credentials are stored.
  4. Store the list securely and tell your trusted person where it is.
  5. Update whenever you add or close an account.
- **No** → *steps*
  1. Identify every account across all platforms.
  2. Decide memorialize / delete / transfer for each.
  3. Write down decisions and store with your digital-access plan.
  4. Ensure login credentials are in your password manager.
  5. Tell your trusted person where to find your instructions.

### D2.2 Have you backed up your photos, videos, and personal files (cloud storage, external drive) AND told your trusted person how to access them?

- **Yes, backed up and access documented** → *review*
  - Checklist: backups current (cloud + external)? access instructions accurate? credentials in password manager? trusted person knows where backup drive is located?
- **Backed up but no access plan (or vice versa)** → *steps*
  1. Confirm photos/videos/files are backed up in cloud and/or external drive.
  2. Document how to access each backup (logins, physical drive location, required apps).
  3. Store access instructions with your digital-access plan or password manager.
  4. Tell your trusted person where the instructions are and how to use them.
  5. Update whenever you change devices or storage locations.
- **No** → *steps*
  1. Choose a cloud storage option and/or external drive.
  2. Back up photos, videos, important files regularly.
  3. Document how to access each backup.
  4. Store login credentials in your password manager.
  5. Tell your trusted person where backup instructions are kept.

### D2.3 Do you own any digital assets that require special access to inherit (cryptocurrency, NFTs, online businesses, paid digital products, domain names, gaming accounts, frequent-flyer miles, hotel points) — and are they documented for your trusted person?

- **Yes, fully documented with secure access plan** → *review*
  - Checklist: assets active/listed? access instructions (wallet keys, logins, recovery phrases) current? credentials in password manager? trusted person knows where documentation is kept?
- **Partially documented or trusted person does not know how to access** → *steps*
  1. List every digital asset (crypto wallets, NFTs, domains, online businesses, digital products, gaming accounts, loyalty points).
  2. Document access instructions per asset (wallet keys, recovery phrases, logins, transfer steps).
  3. Store sensitive info in a password manager or secure physical location.
  4. Tell your trusted person where documentation is and how to use it.
  5. Update whenever you acquire or retire an asset.
- **No** → *steps*
  1. Identify all digital assets you own, including loyalty points and domains.
  2. Write down access instructions and store securely.
  3. Add wallet keys, recovery phrases, logins to your password manager.
  4. Tell your trusted person where your digital-asset plan is stored.
  5. Review annually.
- **Not applicable (no inheritable digital assets)** → *review (no action)*
  - No action needed — but review periodically. Digital assets are easy to accumulate unintentionally (new apps, loyalty programs, online purchases); check once a year.

### D2.4 Have you designated a Digital Asset Manager (the specific person responsible for handling your digital accounts after death) and given them written authority?

- **Yes, named in writing AND legally authorized in my will** → *review*
  - Checklist: named person still preferred? designation stated in will/estate docs? manager knows role/responsibilities? digital-access instructions stored where they can find them?
- **I have picked someone but no written authority** → *steps*
  1. Add a Digital Asset Manager designation to your will or estate plan.
  2. Write down clear instructions for accessing digital accounts.
  3. Store instructions securely; ensure your chosen person knows where they are.
  4. Review your digital-asset list to include everything they'll need.
  5. Update estate documents if your digital footprint changes.
- **No** → *steps*
  1. Choose a trusted person comfortable with tech/digital security.
  2. Add their role to your will or estate documents.
  3. Document your digital accounts and access instructions.
  4. Store everything securely and tell your manager where to find it.
  5. Review annually.

---

## D3 — Accounts managed for others & online presence

### D3.1 Have you documented every digital account or system that someone besides you would need to manage if you suddenly could not (work email, work software, freelance client logins, online accounts you administer for family or volunteer work)?

- **Yes, complete list with access strategy** → *review*
  - Checklist: work/client accounts listed? access instructions accurate + secure? shared/delegated accounts included? trusted person knows where documentation is kept?
- **Partial list or list exists but no access plan** → *steps*
  1. List every account you manage for work, clients, family, volunteer roles (software logins, admin dashboards, shared inboxes, subscription tools).
  2. Add access instructions per account.
  3. Store the list securely with your digital-access plan or password manager.
  4. Tell your trusted person where the list is and how to use it.
  5. Update whenever responsibilities or accounts change.
- **No** → *steps*
  1. Identify all accounts you manage beyond personal ones.
  2. Write down each with access instructions.
  3. Store passwords and recovery codes in a password manager.
  4. Tell your trusted person where your digital-responsibility plan is stored.
  5. Review regularly.
- **Not applicable (I do not manage accounts for others)** → *review (no action)*
  - No action needed — but review annually. People unexpectedly take on digital responsibilities (new job tools, family accounts, volunteer roles).

### D3.2 Have you documented what should happen to your online presence after death (social media memorialization, accounts to delete, content to preserve, final messages to send, channels you want passed on)?

- **Yes, documented with named manager and instructions** → *review*
  - Checklist: accounts listed/active? memorialize/delete/transfer choices still right? final messages / content-preservation notes current? Digital Asset Manager knows where instructions are stored?
- **I have thought about it but nothing documented** → *steps*
  1. List every online platform you use (social media, blogs, communities, content sites).
  2. Decide what happens to each (memorialize, delete, transfer, archive, preserve content).
  3. Write clear instructions, including any final messages/posts.
  4. Store securely and tell your Digital Asset Manager where to find them.
  5. Review annually.
- **No** → *steps*
  1. Identify all your online accounts and platforms.
  2. Decide memorialize / delete / transfer for each.
  3. Document your wishes and store securely.
  4. Tell your Digital Asset Manager or trusted person where instructions are.
  5. Update as your digital footprint changes.
