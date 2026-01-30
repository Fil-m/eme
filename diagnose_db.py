from app import app, db, Page

with app.app_context():
    pages = Page.query.all()
    print(f"Found {len(pages)} pages.")
    for p in pages:
        print(f"Slug: {p.slug}, Title: {p.title}, Content Length: {len(p.content) if p.content else 0}")
        if p.content:
            print(f"First 50 chars: {p.content[:50]}...")
