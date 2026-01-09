import httpx
from app.settings import settings

async def check_apoiase_status(email: str) -> bool:
    if not settings.APOIASE_API_KEY or not settings.APOIASE_API_SECRET:
        print("APOIA.se credentials not set.")
        return False
    
    url = f"https://api.apoia.se/backers/charges/{email}"
    headers = {
        "Accept": "*/*",
        "Content-Type": "application/json",
        "x-api-key": settings.APOIASE_API_KEY,
        "Authorization": f"Bearer {settings.APOIASE_API_SECRET}"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                # Response format: {"isPaidThisMonth":false,"isBacker":false}
                return data.get("isBacker", False)
            else:
                print(f"APOIA.se API returned status {response.status_code}: {response.text}")
        except Exception as e:
            print(f"Error checking APOIA.se status: {e}")
            return False
            
    return False
