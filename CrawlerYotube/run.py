def run_program():
    while True:
        try:
            import main
            break
        except Exception as e:
            print("Loi~:", e)
            print("Chuong trinh chay lai")

# Gọi hàm để chạy chương trình
while 1: run_program()