import cx_Oracle
import os
os.environ["PATH"] = "D:\ORACLE_DB\instantclient_23_6;" + os.environ["PATH"]

# Oracle DB 연결 설정 
def get_connection():
    try:
        conn = cx_Oracle.connect(
            user="김세현",  # Oracle DB 사용자 이름
            password="비밀번호",  # 개인적으로 문의하면 비밀번호 알려드리겠습니다
            dsn="iedb.kangwon.ac.kr"  # 호스트 및 서비스 이름
        )
        return conn
    except cx_Oracle.Error as e:
        print("DB 연결 오류:", e)
        return None

# 로그인 기능
logged_in_customer_id = None

# 로그인 기능
def login():
    global logged_in_customer_id
    conn = get_connection()
    if conn is None:
        return None, None
    
    try:
        cursor = conn.cursor()
        customer_id = input("사용자 ID를 입력하세요: ")
        password = input("비밀번호를 입력하세요: ")

        cursor.execute("""
            SELECT admin FROM customer WHERE customer_ID = :customer_id AND pwd = :password
        """, {"customer_id": customer_id, "password": password})

        user = cursor.fetchone()
        if user:
            print("로그인 성공!")
            logged_in_customer_id = customer_id
            return customer_id, user[0]
        else:
            print("로그인 실패! 사용자 ID 또는 비밀번호를 확인하세요.")
            return None, None
    except cx_Oracle.Error as e:
        print("로그인 오류:", e)
        return None, None
    finally:
        cursor.close()
        conn.close()


# 회원가입 기능
def register_member():
    conn = get_connection()
    if conn is None:
        return
    
    try:
        cursor = conn.cursor()
        # 회원 정보 입력 받기
        customer_id = input("아이디를 입력하세요: ")
        password = input("비밀번호를 입력하세요: ")
        name = input("이름을 입력하세요: ")
        phone = input("전화번호를 입력하세요: ")

        # SQL 실행
        cursor.execute("""
            INSERT INTO customer (customer_ID, pwd, name, phone) 
            VALUES (:customer_id, :pwd, :name, :phone)
        """, {"customer_id": customer_id,"pwd":password, "name": name, "phone": phone})

        conn.commit()
        print("회원가입이 완료되었습니다!")
    except cx_Oracle.Error as e:
        print("회원가입 오류:", e)
    finally:
        cursor.close()
        conn.close()

# 물품 등록 기능
def add_product():
    conn = get_connection()
    if conn is None:
        return

    try:
        cursor = conn.cursor()

        cursor.execute("SELECT NVL(MAX(item_id), 0) + 1 FROM item")
        product_id = cursor.fetchone()[0]

        # 물품 정보 입력 받기
        category = input("종류를 입력하세요: ")
        price = int(input("가격을 입력하세요: "))
        stock = int(input("재고 수량을 입력하세요: "))

        # SQL 실행
        cursor.execute("""
            INSERT INTO item (item_ID, type, price, inventory) 
            VALUES (:item_id, :category, :price, :stock)
        """, {"item_id": product_id, "category": category, "price": price, "stock": stock})

        conn.commit()
        print("물품이 등록되었습니다!")
    except cx_Oracle.Error as e:
        print("물품 등록 오류:", e)
    finally:
        cursor.close()
        conn.close()

# 재고 추가 기능
def add_stock():
    conn = get_connection()
    if conn is None:
        return

    try:
        cursor = conn.cursor()

        # 상품 ID와 추가할 재고 수량 입력 받기
        product_id = int(input("재고를 추가할 물품ID를 입력하세요: "))
        additional_stock = int(input("추가할 재고 수량을 입력하세요: "))

        # 해당 물품이 존재하는지 확인
        cursor.execute("SELECT inventory FROM item WHERE item_ID = :item_id", {"item_id": product_id})
        product = cursor.fetchone()
        if product is None:
            print("해당 물품이 존재하지 않습니다.")
            return

        # 재고 추가
        cursor.execute("""
            UPDATE item SET inventory = inventory + :additional_stock WHERE item_ID = :item_id
        """, {"additional_stock": additional_stock, "item_id": product_id})

        conn.commit()
        print("재고가 추가되었습니다!")
    except cx_Oracle.Error as e:
        print("재고 추가 오류:", e)
    finally:
        cursor.close()
        conn.close()

# 물품 검색 기능
def search_product():
    conn = get_connection()
    if conn is None:
        return

    try:
        cursor = conn.cursor()
        keyword = input("검색할 물품 종류를 입력하세요: ")

        # SQL 실행
        cursor.execute("""
            SELECT * FROM item WHERE type LIKE :keyword
        """, {"keyword": f"%{keyword}%"})

        # 결과 출력
        for row in cursor:
            print(f"물품ID: {row[0]}, 종류: {row[1]}, 가격: {row[2]}, 재고: {row[3]}")
    except cx_Oracle.Error as e:
        print("물품 검색 오류:", e)
    finally:
        cursor.close()
        conn.close()

# 구매 기능
def purchase():
    global logged_in_customer_id
    if logged_in_customer_id is None:
        print("로그인이 필요합니다.")
        return

    conn = get_connection()
    if conn is None:
        return

    try:
        cursor = conn.cursor()

        cursor.execute("SELECT NVL(MAX(buy_id), 0) + 1 FROM buy")
        purchase_id = cursor.fetchone()[0]

        # 구매 정보 입력 받기
        product_id = int(input("물품ID를 입력하세요: "))
        quantity = int(input("주문 수량을 입력하세요: "))
        address = input("배송 주소를 입력하세요: ")

        # 물품 가격 및 할인율 확인 및 결제금액 계산
        cursor.execute("SELECT price, discount FROM item WHERE item_ID = :item_id", {"item_id": product_id})
        price_row = cursor.fetchone()
        if price_row is None:
            print("해당 물품이 존재하지 않습니다.")
            return

        price, item_discount = price_row
        if item_discount is None:
            item_discount = 0

        # 고객 등급별 할인율 확인
        cursor.execute("""
            SELECT discount FROM customer_grade WHERE grade = (
                SELECT grade FROM customer WHERE customer_ID = :customer_id
            )
        """, {"customer_id": logged_in_customer_id})
        grade_discount_row = cursor.fetchone()
        if grade_discount_row is None:
            grade_discount = 0
        else:
            grade_discount = grade_discount_row[0]

        # 최종 할인율 계산
        total_amount = (price * (1 - item_discount/100) * (1 - grade_discount/100))*quantity
        total_discount = (1 - (total_amount / (price * quantity))) * 100

        # 구매 테이블에 추가
        cursor.execute("""
            INSERT INTO buy (buy_id, customer_ID, addr, pay, item_ID, order_num) 
            VALUES (:purchase_id, :customer_id, :address, :total_amount, :item_id, :quantity)
        """, {"purchase_id": purchase_id, "customer_id": logged_in_customer_id, "address": address, "total_amount": total_amount, "item_id": product_id, "quantity": quantity})

        # 물품 재고 감소
        cursor.execute("""
            UPDATE item SET inventory = inventory - :quantity WHERE item_ID = :item_id
        """, {"quantity": quantity, "item_id": product_id})

        # 고객의 총 결제 금액 업데이트
        cursor.execute("""
            UPDATE customer SET pay_amount = NVL(pay_amount, 0) + :total_amount WHERE customer_ID = :customer_id
        """, {"total_amount": total_amount, "customer_id": logged_in_customer_id})

        # 고객의 총 결제 금액 확인
        cursor.execute("SELECT pay_amount FROM customer WHERE customer_ID = :customer_id", {"customer_id": logged_in_customer_id})
        pay_amount = cursor.fetchone()[0]

        # 등급 업데이트
        new_grade = None
        if pay_amount >= 1000000:
            new_grade = "vip"
        elif pay_amount >= 500000:
            new_grade = "gold"
        elif pay_amount >= 100000:
            new_grade = "silver"

        if new_grade:
            cursor.execute("""
                UPDATE customer SET grade = :new_grade WHERE customer_ID = :customer_id
            """, {"new_grade": new_grade, "customer_id": logged_in_customer_id})
            print(f"축하합니다! 등급이 {new_grade}로 상승했습니다.")

        conn.commit()
        print(f"구매가 완료되었습니다! 결제금액: {total_amount}원 (총 할인율: {total_discount}%)")
    except cx_Oracle.Error as e:
        print("구매 오류:", e)
    finally:
        cursor.close()
        conn.close()

# 주문 정보 조회 기능
def view_orders():
    conn = get_connection()
    if conn is None:
        return

    try:
        cursor = conn.cursor()

        # 주문 정보 조회
        cursor.execute("""
            SELECT buy_id, customer_ID, addr, pay, item_ID, order_num
            FROM buy
        """)

        # 결과 출력
        for row in cursor:
            print(f"구매번호: {row[0]}, 고객ID: {row[1]}, 배송주소: {row[2]}, 결제금액: {row[3]}, 물품ID: {row[4]}, 주문수량: {row[5]}")
    except cx_Oracle.Error as e:
        print("주문 정보 조회 오류:", e)
    finally:
        cursor.close()
        conn.close()

# 나의 등급 확인 기능
def view_my_grade():
    global logged_in_customer_id
    if logged_in_customer_id is None:
        print("로그인이 필요합니다.")
        return

    conn = get_connection()
    if conn is None:
        return

    try:
        cursor = conn.cursor()

        # 고객의 등급 조회
        cursor.execute("""
            SELECT grade FROM customer WHERE customer_ID = :customer_id
        """, {"customer_id": logged_in_customer_id})

        grade = cursor.fetchone()
        if grade:
            print(f"현재 등급: {grade[0]}")
        else:
            print("등급 정보를 찾을 수 없습니다.")
    except cx_Oracle.Error as e:
        print("등급 조회 오류:", e)
    finally:
        cursor.close()
        conn.close()


# 할인율 수정 기능
def update_discount():
    conn = get_connection()
    if conn is None:
        return

    try:
        cursor = conn.cursor()

        # 상품 ID와 수정할 할인율 입력 받기
        product_id = int(input("할인율을 수정할 물품ID를 입력하세요: "))
        new_discount = int(input("새로운 할인율을 입력하세요 (%): "))

        # 해당 물품이 존재하는지 확인
        cursor.execute("SELECT item_ID FROM item WHERE item_ID = :item_id", {"item_id": product_id})
        product = cursor.fetchone()
        if product is None:
            print("해당 물품이 존재하지 않습니다.")
            return

        # 할인율 수정
        cursor.execute("""
            UPDATE item SET discount = :new_discount WHERE item_ID = :item_id
        """, {"new_discount": new_discount, "item_id": product_id})

        conn.commit()
        print("할인율이 수정되었습니다!")
    except cx_Oracle.Error as e:
        print("할인율 수정 오류:", e)
    finally:
        cursor.close()
        conn.close()

# 메뉴
if __name__ == "__main__":
    logged_in_user = None
    is_admin = None
    while True:
        if logged_in_user is None:
            print("\n=== 메인 메뉴 ===")
            print("1. 로그인")
            print("2. 회원가입")
            print("0. 종료")
            choice = input("메뉴를 선택하세요: ")

            if choice == "1":
                logged_in_user, is_admin = login()
            elif choice == "2":
                register_member()
            elif choice == "0":
                print("프로그램을 종료합니다.")
                break
            else:
                print("잘못된 입력입니다. 다시 선택해주세요.")
        else:
            if is_admin == 1:
                print("\n=== 관리자 메뉴 ===")
                print("1. 물품 등록")
                print("2. 재고 추가")
                print("3. 물품 검색")
                print("4. 주문 정보 조회")
                print("5. 할인율 수정")
                print("0. 로그아웃")
            else:
                print("\n=== 고객 메뉴 ===")
                print("1. 물품 검색")
                print("2. 구매")
                print("3. 나의 등급 확인")
                print("0. 로그아웃")

            choice = input("메뉴를 선택하세요: ")

            if is_admin == 1:
                if choice == "1":
                    add_product()
                elif choice == "2":
                    add_stock()
                elif choice == "3":
                    search_product()
                elif choice == "4":
                    view_orders()
                elif choice == "5":
                    update_discount()
                elif choice == "0":
                    print("로그아웃합니다.")
                    logged_in_user = None
                    is_admin = None
                else:
                    print("잘못된 입력입니다. 다시 선택해주세요.")
            else:
                if choice == "1":
                    search_product()
                elif choice == "2":
                    purchase()
                elif choice == "3":
                    view_my_grade()
                elif choice == "0":
                    print("로그아웃합니다.")
                    logged_in_user = None
                    is_admin = None
                else:
                    print("잘못된 입력입니다. 다시 선택해주세요.")
