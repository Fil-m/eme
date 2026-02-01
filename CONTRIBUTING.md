# Contributing to EME

Thank you for your interest in the **EME (Experimental Mesh Environment)** project! We are building a "human coral reef" — a digital tool for offline, decentralized community care.

## Principles of Development
When writing code for EME, keep these core principles in mind:

1.  **Offline-First**: Everything MUST work without the internet. No CDNs, no external APIs.
2.  **Simplicity**: The code should be understandable by a junior developer. Avoid over-engineering.
3.  **Low Tech**: The system must run on old laptops and cheap Android phones (via Termux).
4.  **Aesthetics**: The design should be vibrant, organic, and premium. Not "hacker green terminal", but "living reef".

## Development Process

We use a scientific approach to creating new features and solutions:
- Each idea is a hypothesis: "if we add X, then Y will improve (e.g., sync is faster or more people can run a node)".
- We test empirically: on local meshes, with real users, record metrics and feedback (what worked/didn't).
- We iteratively improve based on data, as in daily 1/1 practice.

For implementation, we use Scrum-like practices (adapted to horizontality):
- Self-organized sprints (1–2 weeks): backlog in issues or chat, prioritization together.
- Daily standups: short 1/1 messages in t.me/EME_chat or local groups ("what did/plan/block").
- Retrospectives: weekly lesson reviews (as in manifesto) + feedback on PR. 
- Without a Scrum Master, responsibility is distributed, pull requests are reviewed peer-to-peer.

These are not hard rules, but tools to make changes fast, sustainable, and based on real data.

## How to Contribute

1.  **Fork the repository**.
2.  **Create a branch** for your feature: `git checkout -b feature/amazing-idea`.
3.  **Commit your changes**: `git commit -m 'Add amazing idea'`.
4.  **Push to the branch**: `git push origin feature/amazing-idea`.
5.  **Open a Pull Request**.

## Initial Setup
See [README.md](./README.md) for installation instructions.

## Translations
We aim to be fully bilingual (UA/EN). If you add UI text, please update the dictionary in `app.py`.

---
*“We are not heroes. We are people doing small acts of care for each other.”*
