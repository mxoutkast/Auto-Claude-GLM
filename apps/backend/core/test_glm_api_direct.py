"""Simple GLM API Test
Test the API connection directly to diagnose the issue.
"""
import asyncio
import os
from openai import AsyncOpenAI

async def test_api():
    """Test GLM API directly."""
    api_key = "f58e5fa9671941dc9782311f9d3beba3.slEbdXGe852aSpwn"
    
    print("Testing GLM API Connection...")
    print("=" * 60)
    
    # Test different base URLs
    base_urls = [
        "https://open.bigmodel.cn/api/paas/v4/",
        "https://open.bigmodel.cn/api/paas/v4",
        "https://api.bigmodel.cn/api/paas/v4/",
    ]
    
    models = ["glm-4.7", "glm-4.5-air", "glm-4"]
    
    for base_url in base_urls:
        print(f"\nTesting base_url: {base_url}")
        client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url
        )
        
        for model in models:
            try:
                print(f"  Model: {model}...", end=" ")
                response = await client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": "Say 'test'"}],
                    max_tokens=10
                )
                print(f"✅ SUCCESS")
                print(f"    Response: {response.choices[0].message.content}")
                print(f"    Tokens: {response.usage.total_tokens}")
                await client.close()
                return  # Success, exit
            except Exception as e:
                error_msg = str(e)
                if "1113" in error_msg:
                    print(f"❌ No balance/quota")
                elif "1211" in error_msg:
                    print(f"❌ Model not found")
                elif "401" in error_msg or "Unauthorized" in error_msg:
                    print(f"❌ Auth failed")
                else:
                    print(f"❌ Error: {error_msg[:80]}")
        
        await client.close()
    
    print("\n" + "=" * 60)
    print("All tests failed. Possible issues:")
    print("1. API key might be for a different service (coding tools vs API)")
    print("2. Plan might not include direct API access")
    print("3. Need to activate API access in the dashboard")
    print("\nCheck: https://open.bigmodel.cn/usercenter/apikeys")

if __name__ == "__main__":
    asyncio.run(test_api())
