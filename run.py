from app import create_app

app = create_app()

if __name__ == '__main__':
    #Khi sửa code, web tự động cập nhật không cần chạy lại
    app.run(debug=True)
    print("OK")