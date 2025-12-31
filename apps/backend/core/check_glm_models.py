"""Check Available GLM Models
Test what models are available with the API key.
"""
import asyncio
import os
from openai import AsyncOpenAI

async def test_models():
    """Test different GLM model names."""
    api_key = os.environ.get("ZHIPUAI_API_KEY")
    if not api_key:
        print("❌ ZHIPUAI_API_KEY not set")
        return
    
    client = AsyncOpenAI(
        api_key=api_key,
        base_url="https://open.bigmodel.cn/api/paas/v4/"
    )
    
    # Model names to try
    models_to_try = [
        "glm-4",
        "glm-4-flash",
        "glm-4-plus",
        "glm-4-air",
        "glm-4-0520",
        "glm-4v",
        "glm-4-alltools",
        "glm-4-9b-chat",
    ]
    
    print("Testing GLM Models...")
    print("=" * 60)
    
    for model in models_to_try:
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=10
            )
            print(f"✅ {model:20} - WORKS")
            print(f"   Response: {response.choices[0].message.content}")
        except Exception as e:
            error_msg = str(e)
            if "1211" in error_msg:
                print(f"❌ {model:20} - Model not found")
            else:
                print(f"⚠️  {model:20} - Error: {error_msg[:50]}")
    
    await client.close()

if __name__ == "__main__":
    asyncio.run(test_models())
