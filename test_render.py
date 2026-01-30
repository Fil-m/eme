from app import app, db, Page
import markdown

with app.app_context():
    page = Page.query.filter_by(slug="manifest").first()
    if page:
        print(f"Testing render for: {page.title}")
        try:
            html = markdown.markdown(page.content)
            print(f"Rendered HTML length: {len(html)}")
            print("First 100 chars of HTML:")
            print(html[:100])
        except Exception as e:
            print(f"Error rendering markdown: {e}")
    else:
        print("Page not found.")
