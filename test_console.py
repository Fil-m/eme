import asyncio
from playwright.async_api import async_playwright
import os
import django
import sys

# Setup Django to get a valid token
sys.path.append(r'd:\dev\eme')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eme.settings')
django.setup()

from profiles.models import EMEUser
from rest_framework_simplejwt.tokens import RefreshToken

user = EMEUser.objects.filter(username='admin').first() or EMEUser.objects.filter(is_superuser=True).first() or EMEUser.objects.first()
refresh = RefreshToken.for_user(user)
access_token = str(refresh.access_token)

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        errors = []
        def on_console(msg):
            if msg.type in ['error', 'warning']:
                print(f"[CONSOLE {msg.type.upper()}] {msg.text}")
                errors.append(msg.text)
        
        def on_error(err):
            print(f"[PAGE ERROR] {err}")
            errors.append(str(err))
            
        page.on("console", on_console)
        page.on("pageerror", on_error)
        
        print("Goto localhost:8000...")
        await page.goto("http://localhost:8000")
        
        print("Injecting token...")
        await page.evaluate(f"localStorage.setItem('access_token', '{access_token}');")
        
        print("Reloading to authenticate...")
        await page.goto("http://localhost:8000")
        
        print("Clicking randomly on cards...")
        # Inject an interval to constantly try finding and clicking project cards
        await page.evaluate("""
            setInterval(() => {
                const links = document.querySelectorAll('.nav-link .nav-link-title');
                links.forEach(l => {
                    if(l.innerText.includes('Проекти')) l.parentElement.click();
                });
                
                const cards = document.querySelectorAll('.kanban-card-title');
                if(cards.length > 0) {
                    cards[0].click();
                }
            }, 1000);
        """)
        
        print("Waiting 10 seconds to collect logs...")
        await asyncio.sleep(10)
        
        print("--- EXTRACTED ERRORS ---")
        for e in errors:
            print(" ->", e)

        await browser.close()

asyncio.run(main())
