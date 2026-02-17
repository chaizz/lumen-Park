import asyncio
import httpx

async def test_api():
    async with httpx.AsyncClient() as client:
        try:
            # 测试获取相册列表
            response = await client.get("http://localhost:8000/albums/")
            print(f"Albums API Status: {response.status_code}")
            if response.status_code == 200:
                albums = response.json()
                print(f"Found {len(albums)} albums")
                if albums:
                    album_id = albums[0]['id']
                    print(f"Testing album ID: {album_id}")
                    
                    # 测试获取相册详情
                    detail_response = await client.get(f"http://localhost:8000/albums/{album_id}")
                    print(f"Album Detail API Status: {detail_response.status_code}")
                    if detail_response.status_code == 200:
                        album_detail = detail_response.json()
                        print(f"Album title: {album_detail.get('title')}")
                        posts = album_detail.get('posts', [])
                        print(f"Posts in album: {len(posts)}")
                        if posts:
                            post = posts[0]
                            print(f"First post: {post.get('title')}")
                            print(f"Post image_path: {post.get('image_path')}")
                            print(f"Post images count: {len(post.get('images', []))}")
                            if post.get('images'):
                                print(f"First image path: {post['images'][0].get('image_path')}")
                    else:
                        print(f"Error: {detail_response.text}")
            else:
                print(f"Error: {response.text}")
                
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_api())