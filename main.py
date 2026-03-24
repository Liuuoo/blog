from app import app

if __name__ == "__main__":
    import uvicorn
    print(f">>> 个人博客正在启动于: http://127.0.0.1:10024")
    uvicorn.run(app, host="127.0.0.1", port=10024)
