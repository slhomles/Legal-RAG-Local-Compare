"""
Script tao du lieu mau de test pipeline Tuan 3-4.
Tao 2 file DOCX hop dong (ban goc va ban sua doi) vao thu muc data/raw/
"""
from pathlib import Path

from docx import Document

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)


def main() -> None:
    # --- File 1: Hop_dong_A_v1.docx (Ban goc) ---
    doc1 = Document()
    doc1.add_heading('HOP DONG MUA BAN HANG HOA', level=1)
    doc1.add_paragraph('So: 01/2024/HDMB')
    doc1.add_paragraph('Can cu Luat Thuong mai 2005;')
    doc1.add_paragraph('Can cu nhu cau va kha nang cua hai ben.')

    doc1.add_paragraph('Dieu 1. Dinh nghia')
    doc1.add_paragraph('1.1. "Hang hoa" la san pham dien tu bao gom laptop, may tinh ban va phu kien kem theo.')
    doc1.add_paragraph('1.2. "Ben A" la Cong ty TNHH ABC, dia chi: 123 Nguyen Hue, TP.HCM.')
    doc1.add_paragraph('1.3. "Ben B" la Cong ty CP XYZ, dia chi: 456 Le Loi, Ha Noi.')

    doc1.add_paragraph('Dieu 2. Gia tri hop dong')
    doc1.add_paragraph('2.1. Tong gia tri hop dong la 500.000.000 VND (Nam tram trieu dong).')
    doc1.add_paragraph('2.2. Gia tren da bao gom thue VAT 10%.')
    doc1.add_paragraph('2.3. Phuong thuc thanh toan: Chuyen khoan ngan hang.')

    doc1.add_paragraph('Dieu 3. Thoi gian va dia diem giao hang')
    doc1.add_paragraph('3.1. Thoi gian giao hang: Trong vong 30 ngay ke tu ngay ky hop dong.')
    doc1.add_paragraph('3.2. Dia diem giao hang: Kho hang cua Ben B tai Ha Noi.')
    doc1.add_paragraph('3.3. Chi phi van chuyen do Ben A chiu.')

    doc1.add_paragraph('Dieu 4. Bao hanh')
    doc1.add_paragraph('4.1. Thoi gian bao hanh: 12 thang ke tu ngay giao hang.')
    doc1.add_paragraph('4.2. Ben A chiu trach nhiem sua chua mien phi cac loi do nha san xuat.')

    doc1.add_paragraph('Dieu 5. Phat vi pham')
    doc1.add_paragraph('5.1. Ben nao vi pham hop dong phai boi thuong 8% gia tri hop dong.')
    doc1.add_paragraph('5.2. Truong hop bat kha khang, hai ben se thoa thuan lai.')

    output1 = RAW_DIR / "Hop_dong_A_v1.docx"
    doc1.save(str(output1))
    print(f"Da tao: {output1}")

    # --- File 2: Hop_dong_A_v2.docx (Ban sua doi) ---
    doc2 = Document()
    doc2.add_heading('HOP DONG MUA BAN HANG HOA (SUA DOI LAN 1)', level=1)
    doc2.add_paragraph('So: 01/2024/HDMB - SDBS01')
    doc2.add_paragraph('Can cu Luat Thuong mai 2005;')
    doc2.add_paragraph('Can cu nhu cau va kha nang cua hai ben.')

    doc2.add_paragraph('Dieu 1. Dinh nghia')
    doc2.add_paragraph('1.1. "Hang hoa" la san pham dien tu bao gom laptop, may tinh ban, man hinh va phu kien kem theo.')
    doc2.add_paragraph('1.2. "Ben A" la Cong ty TNHH ABC, dia chi: 123 Nguyen Hue, TP.HCM.')
    doc2.add_paragraph('1.3. "Ben B" la Cong ty CP XYZ, dia chi: 789 Tran Hung Dao, Ha Noi.')

    doc2.add_paragraph('Dieu 2. Gia tri hop dong')
    doc2.add_paragraph('2.1. Tong gia tri hop dong la 650.000.000 VND (Sau tram nam muoi trieu dong).')
    doc2.add_paragraph('2.2. Gia tren da bao gom thue VAT 8%.')
    doc2.add_paragraph('2.3. Phuong thuc thanh toan: Chuyen khoan ngan hang hoac L/C.')

    doc2.add_paragraph('Dieu 3. Thoi gian va dia diem giao hang')
    doc2.add_paragraph('3.1. Thoi gian giao hang: Trong vong 45 ngay ke tu ngay ky hop dong.')
    doc2.add_paragraph('3.2. Dia diem giao hang: Kho hang cua Ben B tai Ha Noi.')
    doc2.add_paragraph('3.3. Chi phi van chuyen do Ben A chiu. Ben A duoc quyen lua chon don vi van chuyen.')

    doc2.add_paragraph('Dieu 4. Bao hanh')
    doc2.add_paragraph('4.1. Thoi gian bao hanh: 24 thang ke tu ngay giao hang.')
    doc2.add_paragraph('4.2. Ben A chiu trach nhiem sua chua mien phi cac loi do nha san xuat.')
    doc2.add_paragraph('4.3. Ben A cung cap duong day nong ho tro ky thuat 24/7.')

    doc2.add_paragraph('Dieu 5. Phat vi pham')
    doc2.add_paragraph('5.1. Ben nao vi pham hop dong phai boi thuong 10% gia tri hop dong.')
    doc2.add_paragraph('5.2. Truong hop bat kha khang, hai ben se thoa thuan lai.')

    doc2.add_paragraph('Dieu 6. Dieu khoan bo sung')
    doc2.add_paragraph('6.1. Moi tranh chap phat sinh se duoc giai quyet tai Trung tam Trong tai Quoc te Viet Nam (VIAC).')

    output2 = RAW_DIR / "Hop_dong_A_v2.docx"
    doc2.save(str(output2))
    print(f"Da tao: {output2}")


if __name__ == "__main__":
    main()
