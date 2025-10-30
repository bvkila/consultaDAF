from credenciais import *
from playwright.sync_api import sync_playwright

def main() -> None:
    
    site_url = url_sharepoint
    storage_state_path = "./storage_state.json"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='msedge', headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto(site_url)
        
        # Wait for network to be idle; login flow may redirect to Microsoft login pages
        page.wait_for_load_state("networkidle")

        print("\nFaça o login no SharePoint e aguarde...")
        input("Quando a página estiver completamente carregada e autorizada, aperte Enter no terminal para continuar...")

        # Persist cookies and related state
        context.storage_state(path=storage_state_path)
        print(f"Saved Playwright storage state to: {storage_state_path}")

        context.close()
        browser.close()

if __name__ == "__main__":
    main()