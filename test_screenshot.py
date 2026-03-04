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
        context = await browser.new_context(viewport={'width': 1280, 'height': 800})
        page = await context.new_page()
        
        print("Goto localhost:8000...")
        await page.goto("http://localhost:8000")
        
        print("Injecting token...")
        await page.evaluate(f"localStorage.setItem('access_token', '{access_token}');")
        
        print("Reloading to authenticate...")
        await page.goto("http://localhost:8000")
        
        print("Clicking Projects tab...")
        await page.wait_for_selector('.nav-link', timeout=5000)
        await page.evaluate("""
            const links = document.querySelectorAll('.nav-link .nav-link-title');
            links.forEach(l => {
                if(l.innerText.includes('Проекти')) l.parentElement.click();
            });
        """)
        
        print("Waiting for Board and taking screenshot 1...")
        await page.wait_for_selector('.kanban-card-title', timeout=5000)
        await page.screenshot(path="d:\\dev\\eme\\before_click.png")
        
        print("Clicking a project card...")
        await page.evaluate("document.querySelector('.kanban-card-title').click()")
        
        print("Waiting 1s and taking screenshot 2...")
        await asyncio.sleep(1)
        await page.screenshot(path="d:\\dev\\eme\\after_click.png")

        print("Waiting 3s and taking screenshot 3...")
        await asyncio.sleep(3)
        await page.screenshot(path="d:\\dev\\eme\\after_3s.png")

        await browser.close()

asyncio.run(main())
