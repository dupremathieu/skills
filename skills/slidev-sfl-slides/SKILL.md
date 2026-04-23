---
name: slidev-sfl-slides
description: Create Savoir-faire Linux branded first and last slides for Slidev presentations. Use when creating presentation slides with SFL branding.
argument-hint: "[title] [event]"
---

# Savoir-faire Linux Slidev Slides Generator

This skill creates branded first and last slides for Slidev presentations using Savoir-faire Linux visual identity.

## Parameters

When invoked, ask the user for:
- **Title**: The presentation title (required)
- **Event**: The event name (required)
- **Author**: Author name (default: "Mathieu Dupré")
- **Author Email**: Author email (default: "mathieu.dupre@savoirfairelinux.com")

## Resources Location

The following resources must be available:
- Logo: `/home/mathieu/Documents/presentation/slide-ressources/savoir-faire-linux-logo.svg`
- Logo (icon only): `/home/mathieu/Documents/presentation/slide-ressources/savoir-faire-linux-logo-only.svg`
- Email icon: `/home/mathieu/Documents/presentation/slide-ressources/emai-icon.svg`
- Front background: `/home/mathieu/Documents/presentation/slide-ressources/background_frontpage.jpg`
- Back background: `/home/mathieu/Documents/presentation/slide-ressources/background_backpage.jpg`

## First Slide Template

Generate this slide at the beginning of the presentation:

```md
---
layout: none
---

<div class="first-slide">
  <img src="/home/mathieu/Documents/presentation/slide-ressources/savoir-faire-linux-logo.svg" class="logo" />
  <h1 class="title">{TITLE}</h1>
  <p class="event">{EVENT}</p>
  <p class="author">{AUTHOR}</p>
</div>

<style>
@import url('https://fonts.googleapis.com/css2?family=Ubuntu:wght@400;500;700&display=swap');

.first-slide {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  font-family: 'Ubuntu', sans-serif;
  background:
    linear-gradient(rgba(1, 81, 106, 0.8), rgba(1, 81, 106, 0.8)),
    url('/home/mathieu/Documents/presentation/slide-ressources/background_frontpage.jpg');
  background-size: cover;
  background-position: center;
}

.first-slide .logo {
  position: absolute;
  top: 40px;
  width: 300px;
}

.first-slide .title {
  color: white;
  font-size: 2.5em;
  font-weight: 700;
  text-align: center;
  margin: 0;
  max-width: 80%;
}

.first-slide .event {
  color: #56b0c9;
  font-size: 1.5em;
  margin-top: 20px;
}

.first-slide .author {
  color: white;
  font-size: 1.2em;
  margin-top: 10px;
}
</style>
```

## Last Slide Template

Generate this slide at the end of the presentation:

```md
---
layout: none
---

<div class="last-slide">
  <img src="/home/mathieu/Documents/presentation/slide-ressources/savoir-faire-linux-logo.svg" class="logo" />
  <h1 class="thanks">Thank you for your attention</h1>
  <p class="author">{AUTHOR}</p>
  <p class="email">{AUTHOR_EMAIL}</p>

  <div class="contact-info">
    <div class="contact-item">
      <img src="/home/mathieu/Documents/presentation/slide-ressources/savoir-faire-linux-logo-only.svg" class="contact-icon" />
      <span>https://savoirfairelinux.com</span>
    </div>
    <div class="contact-item">
      <img src="/home/mathieu/Documents/presentation/slide-ressources/emai-icon.svg" class="contact-icon" />
      <span>contact@savoirfairelinux.com</span>
    </div>
  </div>

  <p class="credits">Graphic designer - Susanne Cuny</p>
</div>

<style>
@import url('https://fonts.googleapis.com/css2?family=Ubuntu:wght@400;500;700&display=swap');

.last-slide {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  font-family: 'Ubuntu', sans-serif;
  background:
    linear-gradient(rgba(1, 81, 106, 0.8), rgba(1, 81, 106, 0.8)),
    url('/home/mathieu/Documents/presentation/slide-ressources/background_backpage.jpg');
  background-size: cover;
  background-position: center;
}

.last-slide .logo {
  position: absolute;
  top: 40px;
  width: 300px;
}

.last-slide .thanks {
  color: white;
  font-size: 2.2em;
  font-weight: 700;
  text-align: center;
  margin: 0;
}

.last-slide .author {
  color: white;
  font-size: 1.3em;
  margin-top: 30px;
  margin-bottom: 5px;
}

.last-slide .email {
  color: white;
  font-size: 1.1em;
  margin: 0;
}

.last-slide .contact-info {
  display: flex;
  gap: 40px;
  margin-top: 40px;
}

.last-slide .contact-item {
  display: flex;
  align-items: center;
  gap: 10px;
  color: white;
  font-size: 0.9em;
}

.last-slide .contact-icon {
  height: 24px;
  width: auto;
}

.last-slide .credits {
  position: absolute;
  bottom: 20px;
  right: 30px;
  color: #b2b2b2;
  font-size: 0.7em;
  margin: 0;
}
</style>
```

## Instructions

1. Ask the user for the required parameters (title, event) and optional ones (author, email)
2. Generate both slides with the provided values replacing the placeholders:
   - `{TITLE}` - presentation title
   - `{EVENT}` - event name
   - `{AUTHOR}` - author name
   - `{AUTHOR_EMAIL}` - author email
3. Insert the first slide at the beginning of slides.md (after frontmatter)
4. Insert the last slide at the end of slides.md
