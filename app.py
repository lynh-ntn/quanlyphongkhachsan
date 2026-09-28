import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date
import os

st.image("VT.jpg")
# =========================================================
# CẤU HÌNH APP
# =========================================================

st.set_page_config(
    page_title="Hotel Room Management",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB_FILE = "hotel.db"


# =========================================================
# DATABASE
# =========================================================

def get_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    conn = get_connection()
    cursor = conn.cursor()

    # Bảng phòng
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_number TEXT UNIQUE NOT NULL,
            room_type TEXT NOT NULL,
            floor INTEGER NOT NULL,
            price REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'Trống',
            note TEXT DEFAULT ''
        )
    """)

    # Bảng đặt phòng
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guest_name TEXT NOT NULL,
            phone TEXT,
            room_number TEXT NOT NULL,
            room_type TEXT,
            check_in TEXT NOT NULL,
            check_out TEXT NOT NULL,
            guests INTEGER DEFAULT 1,
            price_per_night REAL DEFAULT 0,
            total_amount REAL DEFAULT 0,
            status TEXT DEFAULT 'Đã đặt',
            created_at TEXT
        )
    """)

    # Bảng lịch sử
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_number TEXT,
            action TEXT,
            guest_name TEXT,
            amount REAL DEFAULT 0,
            action_time TEXT
        )
    """)

    # Nếu chưa có phòng thì tạo dữ liệu mẫu
    cursor.execute("SELECT COUNT(*) FROM rooms")
    room_count = cursor.fetchone()[0]

    if room_count == 0:
        rooms = [
            ("101", "Standard", 1, 650000, "Trống", ""),
            ("102", "Standard", 1, 650000, "Trống", ""),
            ("103", "Standard", 1, 650000, "Trống", ""),
            ("104", "Standard", 1, 650000, "Trống", ""),
            ("201", "Deluxe", 2, 850000, "Trống", ""),
            ("202", "Deluxe", 2, 850000, "Trống", ""),
            ("203", "Deluxe", 2, 850000, "Trống", ""),
            ("204", "Deluxe", 2, 850000, "Trống", ""),
            ("301", "Superior", 3, 1000000, "Trống", ""),
            ("302", "Superior", 3, 1000000, "Trống", ""),
            ("303", "Superior", 3, 1000000, "Trống", ""),
            ("304", "Superior", 3, 1000000, "Trống", ""),
            ("401", "Suite", 4, 1500000, "Trống", ""),
            ("402", "Suite", 4, 1500000, "Trống", ""),
            ("501", "VIP", 5, 2500000, "Trống", ""),
            ("502", "VIP", 5, 2500000, "Trống", ""),
        ]

        cursor.executemany("""
            INSERT INTO rooms
            (room_number, room_type, floor, price, status, note)
            VALUES (?, ?, ?, ?, ?, ?)
        """, rooms)

    conn.commit()
    conn.close()


init_database()


# =========================================================
# HÀM DATABASE
# =========================================================

def query_df(query, params=()):
    conn = get_connection()
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


def execute_query(query, params=()):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    conn.commit()
    last_id = cursor.lastrowid
    conn.close()
    return last_id


def get_room(room_number):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM rooms WHERE room_number = ?",
        (room_number,)
    )
    room = cursor.fetchone()
    conn.close()
    return room


def update_room_status(room_number, status):
    execute_query(
        "UPDATE rooms SET status = ? WHERE room_number = ?",
        (status, room_number)
    )


def add_history(room_number, action, guest_name="", amount=0):
    execute_query("""
        INSERT INTO history
        (room_number, action, guest_name, amount, action_time)
        VALUES (?, ?, ?, ?, ?)
    """, (
        room_number,
        action,
        guest_name,
        amount,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))


# =========================================================
# FORMAT TIỀN
# =========================================================

def format_money(value):
    return f"{value:,.0f} VNĐ"


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("🏨 HOTEL MANAGER")
st.sidebar.caption("Hệ thống quản lý phòng khách sạn")

menu = st.sidebar.radio(
    "MENU",
    [
        "📊 Tổng quan",
        "🛏️ Quản lý phòng",
        "📅 Đặt phòng",
        "👤 Check-in",
        "🚪 Check-out",
        "🔧 Bảo trì phòng",
        "📜 Lịch sử"
    ]
)

st.sidebar.divider()

st.sidebar.info(
    "💡 Hệ thống sử dụng SQLite nên dữ liệu sẽ được lưu "
    "trong file hotel.db ngay tại thư mục chạy app."
)


# =========================================================
# CSS
# =========================================================

st.markdown("""
<style>
    .main-title {
        font-size: 32px;
        font-weight: 700;
        margin-bottom: 5px;
    }

    .sub-title {
        color: #666;
        margin-bottom: 25px;
    }

    div[data-testid="stMetric"] {
        border: 1px solid #e5e5e5;
        border-radius: 12px;
        padding: 15px;
        background-color: #fafafa;
    }

    .room-card {
        border: 1px solid #ddd;
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 10px;
        background-color: #ffffff;
    }

    .status {
        font-weight: bold;
    }

    .footer {
        text-align: center;
        color: #888;
        margin-top: 40px;
        padding: 20px;
    }
</style>
""", unsafe_allow_html=True)


# =========================================================
# 1. DASHBOARD
# =========================================================

if menu == "📊 Tổng quan":

    st.markdown(
        '<div class="main-title">📊 Tổng quan khách sạn</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="sub-title">Theo dõi tình trạng phòng và hoạt động kinh doanh</div>',
        unsafe_allow_html=True
    )

    rooms_df = query_df("SELECT * FROM rooms")
    bookings_df = query_df("SELECT * FROM bookings")

    total_rooms = len(rooms_df)

    available_rooms = len(
        rooms_df[rooms_df["status"] == "Trống"]
    )

    occupied_rooms = len(
        rooms_df[rooms_df["status"] == "Đang ở"]
    )

    reserved_rooms = len(
        rooms_df[rooms_df["status"] == "Đã đặt"]
    )

    maintenance_rooms = len(
        rooms_df[rooms_df["status"] == "Bảo trì"]
    )

    revenue = bookings_df[
        bookings_df["status"] == "Đã trả phòng"
    ]["total_amount"].sum()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("🏨 Tổng phòng", total_rooms)
    col2.metric("🟢 Phòng trống", available_rooms)
    col3.metric("🔴 Đang có khách", occupied_rooms)
    col4.metric("🟡 Đã đặt", reserved_rooms)

    st.divider()

    col1, col2, col3 = st.columns(3)

    col1.metric("🔧 Bảo trì", maintenance_rooms)
    col2.metric("💰 Doanh thu đã thu", format_money(revenue))
    col3.metric(
        "📈 Công suất phòng",
        f"{(occupied_rooms / total_rooms * 100):.1f}%"
        if total_rooms > 0 else "0%"
    )

    st.divider()

    st.subheader("🛏️ Tình trạng phòng")

    status_count = rooms_df["status"].value_counts()

    col1, col2 = st.columns(2)

    with col1:
        st.bar_chart(status_count)

    with col2:
        status_table = pd.DataFrame({
            "Trạng thái": status_count.index,
            "Số phòng": status_count.values
        })

        st.dataframe(
            status_table,
            use_container_width=True,
            hide_index=True
        )

    st.subheader("📅 Các booking gần đây")

    recent_bookings = query_df("""
        SELECT
            id AS 'Mã',
            guest_name AS 'Khách hàng',
            phone AS 'SĐT',
            room_number AS 'Phòng',
            check_in AS 'Check-in',
            check_out AS 'Check-out',
            total_amount AS 'Tổng tiền',
            status AS 'Trạng thái'
        FROM bookings
        ORDER BY id DESC
        LIMIT 10
    """)

    if len(recent_bookings) > 0:
        st.dataframe(
            recent_bookings,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Chưa có booking nào.")


# =========================================================
# 2. QUẢN LÝ PHÒNG
# =========================================================

elif menu == "🛏️ Quản lý phòng":

    st.markdown(
        '<div class="main-title">🛏️ Quản lý phòng</div>',
        unsafe_allow_html=True
    )

    rooms_df = query_df("SELECT * FROM rooms ORDER BY floor, room_number")

    col1, col2, col3 = st.columns(3)

    with col1:
        search = st.text_input(
            "🔎 Tìm phòng",
            placeholder="Nhập số phòng..."
        )

    with col2:
        status_filter = st.selectbox(
            "Trạng thái",
            [
                "Tất cả",
                "Trống",
                "Đã đặt",
                "Đang ở",
                "Bảo trì",
                "Đang dọn"
            ]
        )

    with col3:
        type_filter = st.selectbox(
            "Loại phòng",
            ["Tất cả"] + sorted(rooms_df["room_type"].unique().tolist())
        )

    filtered = rooms_df.copy()

    if search:
        filtered = filtered[
            filtered["room_number"]
            .astype(str)
            .str.contains(search, case=False)
        ]

    if status_filter != "Tất cả":
        filtered = filtered[
            filtered["status"] == status_filter
        ]

    if type_filter != "Tất cả":
        filtered = filtered[
            filtered["room_type"] == type_filter
        ]

    st.write(f"**Hiển thị {len(filtered)} phòng**")

    # Hiển thị từng phòng
    for _, room in filtered.iterrows():

        col1, col2, col3, col4, col5 = st.columns(
            [1, 1.5, 1, 1.5, 2]
        )

        col1.write(f"### 🛏️ {room['room_number']}")
        col2.write(f"**{room['room_type']}**")
        col3.write(f"Tầng {room['floor']}")
        col4.write(format_money(room["price"]))

        with col5:

            status_options = [
                "Trống",
                "Đã đặt",
                "Đang ở",
                "Bảo trì",
                "Đang dọn"
            ]

            current_index = (
                status_options.index(room["status"])
                if room["status"] in status_options
                else 0
            )

            new_status = st.selectbox(
                "Trạng thái",
                status_options,
                index=current_index,
                key=f"status_{room['room_number']}"
            )

            if new_status != room["status"]:

                update_room_status(
                    room["room_number"],
                    new_status
                )

                add_history(
                    room["room_number"],
                    f"Cập nhật trạng thái: {room['status']} → {new_status}"
                )

                st.success(
                    f"Phòng {room['room_number']} đã được cập nhật."
                )

                st.rerun()

        st.divider()

    st.subheader("➕ Thêm phòng mới")

    with st.form("add_room_form"):

        col1, col2, col3 = st.columns(3)

        with col1:
            room_number = st.text_input(
                "Số phòng",
                placeholder="Ví dụ: 601"
            )

        with col2:
            room_type = st.selectbox(
                "Loại phòng",
                [
                    "Standard",
                    "Superior",
                    "Deluxe",
                    "Suite",
                    "VIP"
                ]
            )

        with col3:
            floor = st.number_input(
                "Tầng",
                min_value=1,
                max_value=50,
                value=1
            )

        col1, col2 = st.columns(2)

        with col1:
            price = st.number_input(
                "Giá phòng / đêm",
                min_value=0,
                value=650000,
                step=50000
            )

        with col2:
            note = st.text_input("Ghi chú")

        submitted = st.form_submit_button(
            "➕ Thêm phòng",
            use_container_width=True
        )

        if submitted:

            if not room_number.strip():
                st.error("Vui lòng nhập số phòng.")

            elif get_room(room_number.strip()):
                st.error("Số phòng này đã tồn tại.")

            else:

                execute_query("""
                    INSERT INTO rooms
                    (room_number, room_type, floor, price, status, note)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    room_number.strip(),
                    room_type,
                    floor,
                    price,
                    "Trống",
                    note
                ))

                st.success(
                    f"Đã thêm phòng {room_number}."
                )

                st.rerun()


# =========================================================
# 3. ĐẶT PHÒNG
# =========================================================

elif menu == "📅 Đặt phòng":

    st.markdown(
        '<div class="main-title">📅 Đặt phòng</div>',
        unsafe_allow_html=True
    )

    rooms_df = query_df("""
        SELECT *
        FROM rooms
        WHERE status = 'Trống'
        ORDER BY room_number
    """)

    if len(rooms_df) == 0:

        st.warning("Hiện không có phòng trống.")

    else:

        with st.form("booking_form"):

            st.subheader("👤 Thông tin khách hàng")

            col1, col2 = st.columns(2)

            with col1:
                guest_name = st.text_input(
                    "Họ và tên khách *"
                )

            with col2:
                phone = st.text_input(
                    "Số điện thoại"
                )

            col1, col2 = st.columns(2)

            with col1:
                room_number = st.selectbox(
                    "Chọn phòng",
                    rooms_df["room_number"].tolist()
                )

            with col2:
                guests = st.number_input(
                    "Số khách",
                    min_value=1,
                    max_value=20,
                    value=1
                )

            col1, col2 = st.columns(2)

            with col1:
                check_in = st.date_input(
                    "Ngày check-in",
                    value=date.today()
                )

            with col2:
                check_out = st.date_input(
                    "Ngày check-out",
                    value=date.today()
                )

            selected_room = get_room(room_number)

            price_per_night = selected_room["price"]

            if check_out > check_in:
                nights = (check_out - check_in).days
            else:
                nights = 0

            total_amount = price_per_night * nights

            st.info(
                f"Giá phòng: **{format_money(price_per_night)} / đêm**  \n"
                f"Số đêm: **{nights}**  \n"
                f"Tổng tiền dự kiến: **{format_money(total_amount)}**"
            )

            submitted = st.form_submit_button(
                "📅 Xác nhận đặt phòng",
                use_container_width=True
            )

            if submitted:

                if not guest_name.strip():
                    st.error("Vui lòng nhập tên khách.")

                elif check_out <= check_in:
                    st.error(
                        "Ngày check-out phải sau ngày check-in."
                    )

                else:

                    execute_query("""
                        INSERT INTO bookings
                        (
                            guest_name,
                            phone,
                            room_number,
                            room_type,
                            check_in,
                            check_out,
                            guests,
                            price_per_night,
                            total_amount,
                            status,
                            created_at
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        guest_name,
                        phone,
                        room_number,
                        selected_room["room_type"],
                        str(check_in),
                        str(check_out),
                        guests,
                        price_per_night,
                        total_amount,
                        "Đã đặt",
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    ))

                    update_room_status(
                        room_number,
                        "Đã đặt"
                    )

                    add_history(
                        room_number,
                        "Đặt phòng",
                        guest_name,
                        total_amount
                    )

                    st.success(
                        f"Đặt phòng {room_number} thành công!"
                    )

                    st.rerun()

    st.divider()

    st.subheader("📋 Danh sách đặt phòng")

    bookings = query_df("""
        SELECT
            id AS 'Mã booking',
            guest_name AS 'Khách',
            phone AS 'SĐT',
            room_number AS 'Phòng',
            check_in AS 'Check-in',
            check_out AS 'Check-out',
            guests AS 'Số khách',
            total_amount AS 'Tổng tiền',
            status AS 'Trạng thái'
        FROM bookings
        WHERE status = 'Đã đặt'
        ORDER BY check_in
    """)

    if len(bookings) > 0:

        st.dataframe(
            bookings,
            use_container_width=True,
            hide_index=True
        )

    else:
        st.info("Chưa có booking sắp tới.")


# =========================================================
# 4. CHECK-IN
# =========================================================

elif menu == "👤 Check-in":

    st.markdown(
        '<div class="main-title">👤 Check-in</div>',
        unsafe_allow_html=True
    )

    bookings = query_df("""
        SELECT *
        FROM bookings
        WHERE status = 'Đã đặt'
        ORDER BY check_in
    """)

    if len(bookings) == 0:

        st.info("Không có booking nào đang chờ check-in.")

    else:

        booking_options = {
            f"#{row['id']} - {row['guest_name']} - Phòng {row['room_number']}":
            row["id"]
            for _, row in bookings.iterrows()
        }

        selected_label = st.selectbox(
            "Chọn booking",
            list(booking_options.keys())
        )

        booking_id = booking_options[selected_label]

        booking = bookings[
            bookings["id"] == booking_id
        ].iloc[0]

        st.divider()

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "👤 Khách",
            booking["guest_name"]
        )

        col2.metric(
            "🛏️ Phòng",
            booking["room_number"]
        )

        col3.metric(
            "💰 Tiền phòng",
            format_money(booking["total_amount"])
        )

        st.write(
            f"**Thời gian:** {booking['check_in']} → "
            f"{booking['check_out']}"
        )

        if st.button(
            "✅ Xác nhận Check-in",
            use_container_width=True,
            type="primary"
        ):

            execute_query("""
                UPDATE bookings
                SET status = 'Đang ở'
                WHERE id = ?
            """, (booking_id,))

            update_room_status(
                booking["room_number"],
                "Đang ở"
            )

            add_history(
                booking["room_number"],
                "Check-in",
                booking["guest_name"],
                booking["total_amount"]
            )

            st.success(
                f"Check-in thành công cho {booking['guest_name']}."
            )

            st.rerun()


# =========================================================
# 5. CHECK-OUT
# =========================================================

elif menu == "🚪 Check-out":

    st.markdown(
        '<div class="main-title">🚪 Check-out</div>',
        unsafe_allow_html=True
    )

    bookings = query_df("""
        SELECT *
        FROM bookings
        WHERE status = 'Đang ở'
        ORDER BY check_out
    """)

    if len(bookings) == 0:

        st.info("Hiện không có khách đang lưu trú.")

    else:

        booking_options = {
            f"#{row['id']} - {row['guest_name']} - Phòng {row['room_number']}":
            row["id"]
            for _, row in bookings.iterrows()
        }

        selected_label = st.selectbox(
            "Chọn khách trả phòng",
            list(booking_options.keys())
        )

        booking_id = booking_options[selected_label]

        booking = bookings[
            bookings["id"] == booking_id
        ].iloc[0]

        st.divider()

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "👤 Khách hàng",
            booking["guest_name"]
        )

        col2.metric(
            "🛏️ Phòng",
            booking["room_number"]
        )

        col3.metric(
            "💰 Tiền phòng",
            format_money(booking["total_amount"])
        )

        st.write(
            f"**Check-in:** {booking['check_in']}"
        )

        st.write(
            f"**Check-out dự kiến:** {booking['check_out']}"
        )

        st.divider()

        st.subheader("💰 Thanh toán")

        col1, col2 = st.columns(2)

        with col1:
            room_charge = st.number_input(
                "Tiền phòng",
                min_value=0,
                value=int(booking["total_amount"]),
                step=50000
            )

        with col2:
            extra_charge = st.number_input(
                "Phụ thu / dịch vụ",
                min_value=0,
                value=0,
                step=50000
            )

        total_payment = room_charge + extra_charge

        st.success(
            f"### Tổng thanh toán: {format_money(total_payment)}"
        )

        if st.button(
            "🚪 Xác nhận Check-out",
            use_container_width=True,
            type="primary"
        ):

            execute_query("""
                UPDATE bookings
                SET
                    status = 'Đã trả phòng',
                    total_amount = ?
                WHERE id = ?
            """, (
                total_payment,
                booking_id
            ))

            # Sau checkout chuyển sang trạng thái đang dọn
            update_room_status(
                booking["room_number"],
                "Đang dọn"
            )

            add_history(
                booking["room_number"],
                "Check-out",
                booking["guest_name"],
                total_payment
            )

            st.success(
                f"Check-out thành công. "
                f"Phòng {booking['room_number']} chuyển sang trạng thái Đang dọn."
            )

            st.rerun()


# =========================================================
# 6. BẢO TRÌ
# =========================================================

elif menu == "🔧 Bảo trì phòng":

    st.markdown(
        '<div class="main-title">🔧 Quản lý bảo trì</div>',
        unsafe_allow_html=True
    )

    rooms_df = query_df("""
        SELECT *
        FROM rooms
        WHERE status = 'Bảo trì'
        ORDER BY room_number
    """)

    st.subheader(
        f"🔧 Đang bảo trì: {len(rooms_df)} phòng"
    )

    if len(rooms_df) > 0:

        st.dataframe(
            rooms_df[
                [
                    "room_number",
                    "room_type",
                    "floor",
                    "price",
                    "status",
                    "note"
                ]
            ].rename(columns={
                "room_number": "Phòng",
                "room_type": "Loại phòng",
                "floor": "Tầng",
                "price": "Giá/đêm",
                "status": "Trạng thái",
                "note": "Ghi chú"
            }),
            use_container_width=True,
            hide_index=True
        )

        room_to_release = st.selectbox(
            "Chọn phòng hoàn tất bảo trì",
            rooms_df["room_number"].tolist()
        )

        if st.button(
            "✅ Hoàn tất bảo trì",
            use_container_width=True
        ):

            update_room_status(
                room_to_release,
                "Trống"
            )

            add_history(
                room_to_release,
                "Hoàn tất bảo trì"
            )

            st.success(
                f"Phòng {room_to_release} đã trở lại trạng thái Trống."
            )

            st.rerun()

    else:

        st.success("🎉 Hiện không có phòng nào đang bảo trì.")

    st.divider()

    st.subheader("🔧 Đưa phòng vào bảo trì")

    available_rooms = query_df("""
        SELECT *
        FROM rooms
        WHERE status IN ('Trống', 'Đang dọn')
        ORDER BY room_number
    """)

    if len(available_rooms) > 0:

        room_number = st.selectbox(
            "Chọn phòng",
            available_rooms["room_number"].tolist()
        )

        maintenance_note = st.text_area(
            "Nội dung bảo trì",
            placeholder="Ví dụ: Máy lạnh không hoạt động..."
        )

        if st.button(
            "🔧 Đưa vào bảo trì",
            use_container_width=True
        ):

            execute_query("""
                UPDATE rooms
                SET
                    status = 'Bảo trì',
                    note = ?
                WHERE room_number = ?
            """, (
                maintenance_note,
                room_number
            ))

            add_history(
                room_number,
                f"Đưa vào bảo trì: {maintenance_note}"
            )

            st.success(
                f"Phòng {room_number} đã chuyển sang Bảo trì."
            )

            st.rerun()

    else:

        st.info(
            "Không có phòng phù hợp để đưa vào bảo trì."
        )


# =========================================================
# 7. LỊCH SỬ
# =========================================================

elif menu == "📜 Lịch sử":

    st.markdown(
        '<div class="main-title">📜 Lịch sử hoạt động</div>',
        unsafe_allow_html=True
    )

    history_df = query_df("""
        SELECT
            id AS 'Mã',
            room_number AS 'Phòng',
            action AS 'Hoạt động',
            guest_name AS 'Khách hàng',
            amount AS 'Số tiền',
            action_time AS 'Thời gian'
        FROM history
        ORDER BY id DESC
    """)

    if len(history_df) > 0:

        st.dataframe(
            history_df,
            use_container_width=True,
            hide_index=True
        )

        st.divider()

        st.subheader("📊 Thống kê hoạt động")

        action_count = history_df["Hoạt động"].value_counts()

        st.bar_chart(action_count)

    else:

        st.info("Chưa có lịch sử hoạt động.")


# =========================================================
# FOOTER
# =========================================================

st.markdown("""
<div class="footer">
    🏨 Hotel Room Management System
    <br>
    Web App quản lý phòng khách sạn
    <br>
    Built with Streamlit + SQLite
</div>
""", unsafe_allow_html=True)
