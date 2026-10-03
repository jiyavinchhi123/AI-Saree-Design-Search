import asyncio
from app.database import SessionLocal
from app.onenote.graph_client import MicrosoftOneNoteClient

async def check():
    c = MicrosoftOneNoteClient()
    db = SessionLocal()
    try:
        token = await c.get_valid_token_for_user('b6ecec459b998637', db)
        print('Token valid:', bool(token), flush=True)
        if token:
            nbs = await c.list_notebooks(token)
            print(f'Notebooks: {len(nbs)}', flush=True)
            for nb in nbs:
                nb_name = nb.get('displayName')
                nb_id = nb.get('id')
                print(f'NB: {nb_name} (id: {nb_id})', flush=True)
                secs = await c.list_sections(nb_id, token)
                print(f'  Sections count: {len(secs)}', flush=True)
                for s in secs:
                    sec_name = s.get('displayName')
                    sec_id = s.get('id')
                    print(f'   Section: {sec_name} (id: {sec_id})', flush=True)
                    pgs = await c.list_pages(sec_id, token)
                    print(f'     Pages count: {len(pgs)}', flush=True)
                    for p in pgs:
                        p_title = p.get('title')
                        p_id = p.get('id')
                        p_client = p.get('links', {}).get('oneNoteClientUrl', {}).get('href')
                        p_web = p.get('links', {}).get('oneNoteWebUrl', {}).get('href')
                        print(f'      Page: {p_title} | ID: {p_id}', flush=True)
                        print(f'        Client URL: {p_client}', flush=True)
                        print(f'        Web URL: {p_web}', flush=True)
    finally:
        db.close()

if __name__ == '__main__':
    asyncio.run(check())
