@router.post("/{product_id}/generate-seo")
async def generate_seo_content(product_id: int):
    from openai import OpenAI
    
    # Fetch product with image
    product = await db.fetch_one("SELECT * FROM products WHERE id = $1", product_id)
    image_url = product['artwork']['image_url']
    
    # Analyze image with GPT-4 Vision
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": "Analyze this t-shirt design. Generate: 1) SEO-optimized title (60 chars max, include style keywords) 2) Description (150-200 words, keyword-rich, persuasive, include material/fit details). Format as JSON: {\"title\": \"...\", \"description\": \"...\"}"},
                {"type": "image_url", "image_url": {"url": image_url}}
            ]
        }],
        max_tokens=500
    )
    
    content = json.loads(response.choices[0].message.content)
    
    # Update product
    await db.execute(
        "UPDATE products SET title = $1, description = $2 WHERE id = $3",
        content['title'], content['description'], product_id
    )
    
    return content
