"""
Tao tap du lieu mau gom 10 cap hop dong tieng Viet voi cac loai thay doi da biet.
Moi cap tao 2 file DOCX (v1, v2) va 1 file JSON ground truth.

Do kho:
  easy   - Hop_dong_A, B, C: thay doi ro rang (so lieu, them/xoa dieu khoan)
  medium - Hop_dong_D, E, F, G: sua tu ngu, doi so lieu + don vi, them dieu khoan moi
  hard   - Hop_dong_H, I, J: them/xoa doan dai, thay doi ngu nghia tu ngu gan giong
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from docx import Document

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
GT_DIR  = Path(__file__).resolve().parents[2] / "data" / "ground_truth"
RAW_DIR.mkdir(parents=True, exist_ok=True)
GT_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _add_paragraphs(doc: Document, paragraphs: List[str]) -> None:
    for p in paragraphs:
        doc.add_paragraph(p)


def _create_docx_pair(
    doc_id: str,
    title_v1: str,
    title_v2: str,
    header_paras: List[str],
    clauses_v1: List[Dict[str, Any]],
    clauses_v2: List[Dict[str, Any]],
) -> None:
    """
    Tao cap file DOCX v1/v2 tu danh sach dict clause.

    Moi clause co dang:
        {"heading": "Dieu X. ...", "paragraphs": ["noi dung 1", "noi dung 2", ...]}
    """
    for version, title, clauses in [("v1", title_v1, clauses_v1), ("v2", title_v2, clauses_v2)]:
        doc = Document()
        doc.add_heading(title, level=1)
        _add_paragraphs(doc, header_paras)
        for clause in clauses:
            doc.add_paragraph(clause["heading"])
            _add_paragraphs(doc, clause["paragraphs"])
        out_path = RAW_DIR / f"{doc_id}_{version}.docx"
        doc.save(str(out_path))
        print(f"Da tao: {out_path}")


def _write_ground_truth(
    doc_id: str,
    difficulty: str,
    description: str,
    changes: List[Dict[str, Any]],
    version_old: str = "v1",
    version_new: str = "v2",
) -> None:
    """Ghi file JSON ground truth vao data/ground_truth/."""
    gt = {
        "doc_id": doc_id,
        "version_old": version_old,
        "version_new": version_new,
        "difficulty": difficulty,
        "description": description,
        "changes": changes,
    }
    out_path = GT_DIR / f"{doc_id}_ground_truth.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(gt, f, ensure_ascii=False, indent=2)
    print(f"Da tao: {out_path}")


# ---------------------------------------------------------------------------
# Hop_dong_A  (easy, 6 thay doi) — giu nguyen logic cu
# ---------------------------------------------------------------------------

def _create_hop_dong_a() -> None:
    header = [
        "So: 01/2024/HDMB",
        "Can cu Luat Thuong mai 2005;",
        "Can cu nhu cau va kha nang cua hai ben.",
    ]
    clauses_v1 = [
        {
            "heading": "Dieu 1. Dinh nghia",
            "paragraphs": [
                '1.1. "Hang hoa" la san pham dien tu bao gom laptop, may tinh ban va phu kien kem theo.',
                '1.2. "Ben A" la Cong ty TNHH ABC, dia chi: 123 Nguyen Hue, TP.HCM.',
                '1.3. "Ben B" la Cong ty CP XYZ, dia chi: 456 Le Loi, Ha Noi.',
            ],
        },
        {
            "heading": "Dieu 2. Gia tri hop dong",
            "paragraphs": [
                "2.1. Tong gia tri hop dong la 500.000.000 VND (Nam tram trieu dong).",
                "2.2. Gia tren da bao gom thue VAT 10%.",
                "2.3. Phuong thuc thanh toan: Chuyen khoan ngan hang.",
            ],
        },
        {
            "heading": "Dieu 3. Thoi gian va dia diem giao hang",
            "paragraphs": [
                "3.1. Thoi gian giao hang: Trong vong 30 ngay ke tu ngay ky hop dong.",
                "3.2. Dia diem giao hang: Kho hang cua Ben B tai Ha Noi.",
                "3.3. Chi phi van chuyen do Ben A chiu.",
            ],
        },
        {
            "heading": "Dieu 4. Bao hanh",
            "paragraphs": [
                "4.1. Thoi gian bao hanh: 12 thang ke tu ngay giao hang.",
                "4.2. Ben A chiu trach nhiem sua chua mien phi cac loi do nha san xuat.",
            ],
        },
        {
            "heading": "Dieu 5. Phat vi pham",
            "paragraphs": [
                "5.1. Ben nao vi pham hop dong phai boi thuong 8% gia tri hop dong.",
                "5.2. Truong hop bat kha khang, hai ben se thoa thuan lai.",
            ],
        },
    ]
    clauses_v2 = [
        {
            "heading": "Dieu 1. Dinh nghia",
            "paragraphs": [
                '1.1. "Hang hoa" la san pham dien tu bao gom laptop, may tinh ban, man hinh va phu kien kem theo.',
                '1.2. "Ben A" la Cong ty TNHH ABC, dia chi: 123 Nguyen Hue, TP.HCM.',
                '1.3. "Ben B" la Cong ty CP XYZ, dia chi: 789 Tran Hung Dao, Ha Noi.',
            ],
        },
        {
            "heading": "Dieu 2. Gia tri hop dong",
            "paragraphs": [
                "2.1. Tong gia tri hop dong la 650.000.000 VND (Sau tram nam muoi trieu dong).",
                "2.2. Gia tren da bao gom thue VAT 8%.",
                "2.3. Phuong thuc thanh toan: Chuyen khoan ngan hang hoac L/C.",
            ],
        },
        {
            "heading": "Dieu 3. Thoi gian va dia diem giao hang",
            "paragraphs": [
                "3.1. Thoi gian giao hang: Trong vong 45 ngay ke tu ngay ky hop dong.",
                "3.2. Dia diem giao hang: Kho hang cua Ben B tai Ha Noi.",
                "3.3. Chi phi van chuyen do Ben A chiu. Ben A duoc quyen lua chon don vi van chuyen.",
            ],
        },
        {
            "heading": "Dieu 4. Bao hanh",
            "paragraphs": [
                "4.1. Thoi gian bao hanh: 24 thang ke tu ngay giao hang.",
                "4.2. Ben A chiu trach nhiem sua chua mien phi cac loi do nha san xuat.",
                "4.3. Ben A cung cap duong day nong ho tro ky thuat 24/7.",
            ],
        },
        {
            "heading": "Dieu 5. Phat vi pham",
            "paragraphs": [
                "5.1. Ben nao vi pham hop dong phai boi thuong 10% gia tri hop dong.",
                "5.2. Truong hop bat kha khang, hai ben se thoa thuan lai.",
            ],
        },
        {
            "heading": "Dieu 6. Dieu khoan bo sung",
            "paragraphs": [
                "6.1. Moi tranh chap phat sinh se duoc giai quyet tai Trung tam Trong tai Quoc te Viet Nam (VIAC).",
            ],
        },
    ]
    _create_docx_pair(
        "Hop_dong_A",
        "HOP DONG MUA BAN HANG HOA",
        "HOP DONG MUA BAN HANG HOA (SUA DOI LAN 1)",
        header, clauses_v1, clauses_v2,
    )
    _write_ground_truth(
        "Hop_dong_A", "easy",
        "Hop dong mua ban hang hoa dien tu - 5 sua doi va 1 them moi",
        [
            {"clause_id": "dieu_1", "type": "SUA",
             "description": "Them 'man hinh' vao danh sach hang hoa; thay doi dia chi Ben B",
             "old_text_hint": "laptop, may tinh ban va phu kien", "new_text_hint": "laptop, may tinh ban, man hinh"},
            {"clause_id": "dieu_2", "type": "SUA",
             "description": "Gia tri tang 500M len 650M, VAT 10% xuong 8%, them phuong thuc L/C",
             "old_text_hint": "500.000.000", "new_text_hint": "650.000.000"},
            {"clause_id": "dieu_3", "type": "SUA",
             "description": "Thoi gian giao hang tang 30 len 45 ngay; Ben A duoc lua chon nha van chuyen",
             "old_text_hint": "30 ngay", "new_text_hint": "45 ngay"},
            {"clause_id": "dieu_4", "type": "SUA",
             "description": "Bao hanh tang 12 len 24 thang; them duong day nong 24/7",
             "old_text_hint": "12 thang", "new_text_hint": "24 thang"},
            {"clause_id": "dieu_5", "type": "SUA",
             "description": "Muc phat tang 8% len 10%",
             "old_text_hint": "8%", "new_text_hint": "10%"},
            {"clause_id": "dieu_6", "type": "THEM",
             "description": "Them dieu khoan giai quyet tranh chap qua VIAC"},
        ],
    )


# ---------------------------------------------------------------------------
# Hop_dong_B  (easy, 3 thay doi) — dich vu IT
# ---------------------------------------------------------------------------

def _create_hop_dong_b() -> None:
    header = ["So: 05/2024/HDCNTT", "Can cu Luat Cong nghe thong tin 2006;"]
    clauses_v1 = [
        {
            "heading": "Dieu 1. Thong tin cac ben",
            "paragraphs": [
                '1.1. "Ben cung cap" la Cong ty CP Giai Phap Cong Nghe DEF, so dien thoai: 028.1234.5678.',
                '1.2. "Ben su dung" la Cong ty TNHH GHI, dia chi: 99 Ba Trieu, Ha Noi.',
            ],
        },
        {
            "heading": "Dieu 2. Phi dich vu",
            "paragraphs": [
                "2.1. Phi trien khai ban dau: 100.000.000 VND.",
                "2.2. Phi bao tri hang nam: 20.000.000 VND.",
                "2.3. Thanh toan truoc 30 ngay ke tu ngay xuat hoa don.",
            ],
        },
        {
            "heading": "Dieu 3. Muc do dich vu",
            "paragraphs": [
                "3.1. Do on dinh he thong: toi thieu 99% uptime hang thang.",
                "3.2. Thoi gian xu ly su co: trong vong 4 gio lam viec.",
            ],
        },
        {
            "heading": "Dieu 4. Thoi han hop dong",
            "paragraphs": [
                "4.1. Hop dong co hieu luc trong 1 nam ke tu ngay ky.",
                "4.2. Tu dong gia han neu khong co thong bao cham dut truoc 30 ngay.",
            ],
        },
    ]
    clauses_v2 = [
        {
            "heading": "Dieu 1. Thong tin cac ben",
            "paragraphs": [
                '1.1. "Ben cung cap" la Cong ty CP Giai Phap Cong Nghe DEF, so dien thoai: 024.9876.5432.',
                '1.2. "Ben su dung" la Cong ty TNHH GHI, dia chi: 99 Ba Trieu, Ha Noi.',
            ],
        },
        {
            "heading": "Dieu 2. Phi dich vu",
            "paragraphs": [
                "2.1. Phi trien khai ban dau: 120.000.000 VND.",
                "2.2. Phi bao tri hang nam: 20.000.000 VND.",
                "2.3. Thanh toan truoc 30 ngay ke tu ngay xuat hoa don.",
            ],
        },
        {
            "heading": "Dieu 3. Muc do dich vu",
            "paragraphs": [
                "3.1. Do on dinh he thong: toi thieu 99% uptime hang thang.",
                "3.2. Thoi gian xu ly su co: trong vong 4 gio lam viec.",
            ],
        },
        {
            "heading": "Dieu 4. Thoi han hop dong",
            "paragraphs": [
                "4.1. Hop dong co hieu luc trong 1 nam ke tu ngay ky.",
                "4.2. Tu dong gia han neu khong co thong bao cham dut truoc 30 ngay.",
            ],
        },
        {
            "heading": "Dieu 5. Bao mat thong tin",
            "paragraphs": [
                "5.1. Ben cung cap cam ket bao mat toan bo du lieu cua Ben su dung.",
                "5.2. Khong duoc cung cap thong tin cho ben thu ba khi chua co su dong y bang van ban.",
                "5.3. Nghia vu bao mat ton tai 3 nam sau khi hop dong cham dut.",
            ],
        },
    ]
    _create_docx_pair(
        "Hop_dong_B",
        "HOP DONG DICH VU CONG NGHE THONG TIN",
        "HOP DONG DICH VU CONG NGHE THONG TIN (SUA DOI)",
        header, clauses_v1, clauses_v2,
    )
    _write_ground_truth(
        "Hop_dong_B", "easy",
        "Hop dong dich vu CNTT - thay doi so dien thoai, phi dich vu va them dieu khoan bao mat",
        [
            {"clause_id": "dieu_1", "type": "SUA",
             "description": "So dien thoai Ben cung cap thay doi 028.1234.5678 thanh 024.9876.5432",
             "old_text_hint": "028.1234.5678", "new_text_hint": "024.9876.5432"},
            {"clause_id": "dieu_2", "type": "SUA",
             "description": "Phi trien khai tang tu 100 trieu len 120 trieu VND",
             "old_text_hint": "100.000.000", "new_text_hint": "120.000.000"},
            {"clause_id": "dieu_5", "type": "THEM",
             "description": "Them moi dieu khoan bao mat thong tin (3 khoan)"},
        ],
    )


# ---------------------------------------------------------------------------
# Hop_dong_C  (easy, 2 thay doi) — thue van phong
# ---------------------------------------------------------------------------

def _create_hop_dong_c() -> None:
    header = ["So: 12/2024/HDTVP", "Can cu Luat Kinh doanh bat dong san 2014;"]
    clauses_v1 = [
        {
            "heading": "Dieu 1. Doi tuong hop dong",
            "paragraphs": [
                "1.1. Ben cho thue cho thue van phong tang 5, toa nha Hoang Gia, 88 Ly Thuong Kiet.",
                "1.2. Dien tich thue: 200 m2.",
            ],
        },
        {
            "heading": "Dieu 2. Gia thue va dat coc",
            "paragraphs": [
                "2.1. Gia thue: 15.000.000 VND/thang.",
                "2.2. Dat coc: 3 thang tien thue (45.000.000 VND), tra lai khi het hop dong.",
                "2.3. Tien thue thanh toan vao ngay 5 hang thang.",
            ],
        },
        {
            "heading": "Dieu 3. Thoi han thue",
            "paragraphs": [
                "3.1. Thoi han thue: 24 thang ke tu 01/03/2024.",
                "3.2. Uu tien gia han cho Ben thue neu co nhu cau.",
            ],
        },
        {
            "heading": "Dieu 4. Dat coc bao dam rieng",
            "paragraphs": [
                "4.1. Ngoai dat coc o Dieu 2, Ben thue phai nop them 10.000.000 VND bao dam thiet bi.",
                "4.2. Khoan bao dam nay se hoan tra sau khi nghiem thu thiet bi khi tra phong.",
            ],
        },
        {
            "heading": "Dieu 5. Quyen va nghia vu cac ben",
            "paragraphs": [
                "5.1. Ben thue co quyen su dung van phong va cac tien ich chung.",
                "5.2. Ben thue khong duoc cai tao, sua chua khi chua co su dong y bang van ban.",
            ],
        },
    ]
    clauses_v2 = [
        {
            "heading": "Dieu 1. Doi tuong hop dong",
            "paragraphs": [
                "1.1. Ben cho thue cho thue van phong tang 5, toa nha Hoang Gia, 88 Ly Thuong Kiet.",
                "1.2. Dien tich thue: 200 m2.",
            ],
        },
        {
            "heading": "Dieu 2. Gia thue va dat coc",
            "paragraphs": [
                "2.1. Gia thue: 18.000.000 VND/thang.",
                "2.2. Dat coc: 3 thang tien thue (54.000.000 VND), tra lai khi het hop dong.",
                "2.3. Tien thue thanh toan vao ngay 5 hang thang.",
            ],
        },
        {
            "heading": "Dieu 3. Thoi han thue",
            "paragraphs": [
                "3.1. Thoi han thue: 24 thang ke tu 01/03/2024.",
                "3.2. Uu tien gia han cho Ben thue neu co nhu cau.",
            ],
        },
        {
            "heading": "Dieu 5. Quyen va nghia vu cac ben",
            "paragraphs": [
                "5.1. Ben thue co quyen su dung van phong va cac tien ich chung.",
                "5.2. Ben thue khong duoc cai tao, sua chua khi chua co su dong y bang van ban.",
            ],
        },
    ]
    _create_docx_pair(
        "Hop_dong_C",
        "HOP DONG THUE VAN PHONG",
        "HOP DONG THUE VAN PHONG (SUA DOI)",
        header, clauses_v1, clauses_v2,
    )
    _write_ground_truth(
        "Hop_dong_C", "easy",
        "Hop dong thue van phong - tang gia thue va xoa dieu khoan dat coc bao dam rieng",
        [
            {"clause_id": "dieu_2", "type": "SUA",
             "description": "Gia thue tang 15 trieu len 18 trieu VND/thang; dat coc dieu chinh theo",
             "old_text_hint": "15.000.000", "new_text_hint": "18.000.000"},
            {"clause_id": "dieu_4", "type": "XOA",
             "description": "Xoa hoan toan dieu khoan dat coc bao dam thiet bi rieng"},
        ],
    )


# ---------------------------------------------------------------------------
# Hop_dong_D  (medium, 4 thay doi) — thi cong xay dung
# ---------------------------------------------------------------------------

def _create_hop_dong_d() -> None:
    header = ["So: 07/2024/HDTC", "Can cu Luat Xay dung 2014 (sua doi 2020);"]
    clauses_v1 = [
        {
            "heading": "Dieu 1. Pham vi cong viec",
            "paragraphs": [
                "1.1. Nha thau thi cong he thong dien va nuoc cho toa nha 5 tang tai 55 Nguyen Du.",
                "1.2. Cong viec bao gom: lap dat dien, nuoc, PCCC.",
            ],
        },
        {
            "heading": "Dieu 2. Gia tri hop dong",
            "paragraphs": [
                "2.1. Gia tri hop dong: 2.500.000.000 VND.",
                "2.2. Don gia co dinh, khong dieu chinh trong qua trinh thi cong.",
            ],
        },
        {
            "heading": "Dieu 3. Tien do thi cong",
            "paragraphs": [
                "3.1. Khoi cong: 15/04/2024.",
                "3.2. Hoan thanh: 15/10/2024 (6 thang).",
                "3.3. Ban giao cong trinh khong muon hon 15/10/2024.",
            ],
        },
        {
            "heading": "Dieu 4. Thanh toan",
            "paragraphs": [
                "4.1. Tam ung 30% gia tri hop dong khi ky hop dong.",
                "4.2. Thanh toan dot 2 (50%) khi hoan thanh 70% khoi luong.",
                "4.3. Quyet toan sau nghiem thu.",
            ],
        },
        {
            "heading": "Dieu 5. Phat vi pham tien do",
            "paragraphs": [
                "5.1. Tre tien do moi ngay phat 0,05% gia tri hop dong.",
                "5.2. Muc phat toi da 5% gia tri hop dong.",
            ],
        },
    ]
    clauses_v2 = [
        {
            "heading": "Dieu 1. Pham vi cong viec",
            "paragraphs": [
                "1.1. Nha thau thi cong he thong dien, nuoc, thong gio va dieu hoa khong khi cho toa nha 5 tang tai 55 Nguyen Du.",
                "1.2. Cong viec bao gom: lap dat dien, nuoc, PCCC, thong gio va he thong lanh.",
            ],
        },
        {
            "heading": "Dieu 2. Gia tri hop dong",
            "paragraphs": [
                "2.1. Gia tri hop dong: 2.500.000.000 VND.",
                "2.2. Don gia co dinh, khong dieu chinh trong qua trinh thi cong.",
            ],
        },
        {
            "heading": "Dieu 3. Tien do thi cong",
            "paragraphs": [
                "3.1. Khoi cong: 15/04/2024.",
                "3.2. Hoan thanh: 15/12/2024 (8 thang).",
                "3.3. Ban giao cong trinh khong muon hon 15/12/2024.",
            ],
        },
        {
            "heading": "Dieu 4. Thanh toan",
            "paragraphs": [
                "4.1. Tam ung 30% gia tri hop dong khi ky hop dong.",
                "4.2. Thanh toan dot 2 (50%) khi hoan thanh 70% khoi luong.",
                "4.3. Quyet toan sau nghiem thu.",
            ],
        },
        {
            "heading": "Dieu 4b. Nghiem thu cong viec",
            "paragraphs": [
                "4b.1. Hai ben to chuc nghiem thu tung phan hang thang.",
                "4b.2. Bien ban nghiem thu la co so thanh toan dot tiep theo.",
                "4b.3. Nha thau phai sua chua cac hang muc khong dat truoc khi nghiem thu chinh thuc.",
            ],
        },
        {
            "heading": "Dieu 5. Phat vi pham tien do",
            "paragraphs": [
                "5.1. Tre tien do moi ngay phat 0,05% gia tri hop dong.",
                "5.2. Muc phat toi da 5% gia tri hop dong.",
            ],
        },
    ]
    _create_docx_pair(
        "Hop_dong_D",
        "HOP DONG THI CONG XAY DUNG",
        "HOP DONG THI CONG XAY DUNG (SUA DOI)",
        header, clauses_v1, clauses_v2,
    )
    _write_ground_truth(
        "Hop_dong_D", "medium",
        "Hop dong thi cong - mo rong pham vi cong viec, keo dai tien do, them dieu khoan nghiem thu",
        [
            {"clause_id": "dieu_1", "type": "SUA",
             "description": "Mo rong pham vi: them he thong thong gio va dieu hoa",
             "old_text_hint": "dien va nuoc", "new_text_hint": "dien, nuoc, thong gio va dieu hoa"},
            {"clause_id": "dieu_3", "type": "SUA",
             "description": "Thoi gian hoan thanh keo dai tu 6 thang (10/2024) len 8 thang (12/2024)",
             "old_text_hint": "15/10/2024", "new_text_hint": "15/12/2024"},
            {"clause_id": "dieu_4b", "type": "THEM",
             "description": "Them dieu khoan nghiem thu cong viec dinh ky hang thang"},
            {"clause_id": "dieu_5", "type": "SUA",
             "description": "Khong thay doi - kiem tra false positive"},
        ],
    )


# ---------------------------------------------------------------------------
# Hop_dong_E  (medium, 5 thay doi) — tu van phap ly
# ---------------------------------------------------------------------------

def _create_hop_dong_e() -> None:
    header = ["So: 03/2024/HDTVPL", "Can cu Luat Luat su 2006 (sua doi 2012);"]
    clauses_v1 = [
        {
            "heading": "Dieu 1. Noi dung dich vu tu van",
            "paragraphs": [
                "1.1. Luat su tu van ve hop dong thuong mai va tranh chap dan su.",
                "1.2. Tu van toi da 10 gio/thang; vuot gio tinh them phi.",
            ],
        },
        {
            "heading": "Dieu 2. Phi tu van",
            "paragraphs": [
                "2.1. Phi co dinh: 200.000.000 VND/nam.",
                "2.2. Phi thanh toan chia lam 4 dot bang nhau hang quy.",
            ],
        },
        {
            "heading": "Dieu 3. Thoi han hop dong",
            "paragraphs": [
                "3.1. Thoi han: 6 thang ke tu ngay 01/01/2024.",
                "3.2. Co the gia han theo thoa thuan bang van ban.",
            ],
        },
        {
            "heading": "Dieu 4. Quyen va nghia vu Luat su",
            "paragraphs": [
                "4.1. Luat su co nghia vu bao mat thong tin Khach hang.",
                "4.2. Cung cap y kien phap ly trong vong 5 ngay lam viec.",
            ],
        },
    ]
    clauses_v2 = [
        {
            "heading": "Dieu 1. Noi dung dich vu tu van",
            "paragraphs": [
                "1.1. Luat su tu van ve hop dong thuong mai, tranh chap dan su va lao dong.",
                "1.2. Tu van toi da 15 gio/thang; vuot gio tinh them phi.",
                "1.3. Tham gia to tung tai Toa an khi Khach hang yeu cau, phi tinh rieng.",
            ],
        },
        {
            "heading": "Dieu 2. Phi tu van",
            "paragraphs": [
                "2.1. Phi co dinh: 250.000.000 VND/nam.",
                "2.2. Phi thanh toan chia lam 4 dot bang nhau hang quy.",
            ],
        },
        {
            "heading": "Dieu 3. Thoi han hop dong",
            "paragraphs": [
                "3.1. Thoi han: 12 thang ke tu ngay 01/01/2024.",
                "3.2. Co the gia han theo thoa thuan bang van ban.",
            ],
        },
        {
            "heading": "Dieu 4. Quyen va nghia vu Luat su",
            "paragraphs": [
                "4.1. Luat su co nghia vu bao mat thong tin Khach hang.",
                "4.2. Cung cap y kien phap ly trong vong 5 ngay lam viec.",
            ],
        },
        {
            "heading": "Dieu 5. Bao mat va quyen so huu tri tue",
            "paragraphs": [
                "5.1. Moi thong tin, tai lieu Khach hang cung cap duoc bao mat tuyet doi.",
                "5.2. Luat su khong duoc su dung thong tin Khach hang cho muc dich khac.",
            ],
        },
        {
            "heading": "Dieu 6. Quyen so huu tri tue",
            "paragraphs": [
                "6.1. Moi y kien phap ly, bai phan tich thuoc quyen so huu cua Khach hang sau khi thanh toan.",
                "6.2. Luat su duoc giu lai mot ban sao phuc vu luu tru ho so.",
            ],
        },
    ]
    _create_docx_pair(
        "Hop_dong_E",
        "HOP DONG DICH VU TU VAN PHAP LY",
        "HOP DONG DICH VU TU VAN PHAP LY (SUA DOI)",
        header, clauses_v1, clauses_v2,
    )
    _write_ground_truth(
        "Hop_dong_E", "medium",
        "Hop dong tu van phap ly - mo rong noi dung dich vu, tang phi, gia han thoi han",
        [
            {"clause_id": "dieu_1", "type": "SUA",
             "description": "Mo rong pham vi: them tu van lao dong va to tung; tang gio len 15h/thang",
             "old_text_hint": "10 gio/thang", "new_text_hint": "15 gio/thang"},
            {"clause_id": "dieu_2", "type": "SUA",
             "description": "Phi tu van tang 200 trieu len 250 trieu VND/nam",
             "old_text_hint": "200.000.000", "new_text_hint": "250.000.000"},
            {"clause_id": "dieu_3", "type": "SUA",
             "description": "Thoi han hop dong tang tu 6 thang len 12 thang",
             "old_text_hint": "6 thang", "new_text_hint": "12 thang"},
            {"clause_id": "dieu_5", "type": "THEM",
             "description": "Them dieu khoan bao mat va quyen so huu tri tue"},
            {"clause_id": "dieu_6", "type": "THEM",
             "description": "Them dieu khoan quyen so huu tri tue doi voi y kien phap ly"},
        ],
    )


# ---------------------------------------------------------------------------
# Hop_dong_F  (medium, 4 thay doi) — mua ban thiet bi cong nghiep
# ---------------------------------------------------------------------------

def _create_hop_dong_f() -> None:
    header = ["So: 09/2024/HDMB-CN", "Can cu Luat Thuong mai 2005;"]
    clauses_v1 = [
        {
            "heading": "Dieu 1. Hang hoa va so luong",
            "paragraphs": [
                "1.1. May bom cong nghiep model HP-500: 10 cai.",
                "1.2. Day chuyen dong goi tu dong XK-200: 2 bo.",
            ],
        },
        {
            "heading": "Dieu 2. Gia ca va thanh toan",
            "paragraphs": [
                "2.1. Don gia may bom: 50.000.000 VND/cai.",
                "2.2. Don gia day chuyen dong goi: 800.000.000 VND/bo.",
                "2.3. Tong gia tri: 2.100.000.000 VND.",
                "2.4. Thanh toan bang VND, chuyen khoan.",
            ],
        },
        {
            "heading": "Dieu 3. Uu dai va chiet khau",
            "paragraphs": [
                "3.1. Chiet khau 5% neu dat hang tu 20 cai may bom tro len.",
                "3.2. Mien phi van chuyen cho don hang tren 500 trieu VND.",
            ],
        },
        {
            "heading": "Dieu 4. Giao hang va lap dat",
            "paragraphs": [
                "4.1. Giao hang trong vong 60 ngay ke tu ngay thanh toan.",
                "4.2. Nguoi ban ho tro lap dat mien phi tai cong trinh Ben mua.",
            ],
        },
    ]
    clauses_v2 = [
        {
            "heading": "Dieu 1. Hang hoa va so luong",
            "paragraphs": [
                "1.1. May bom cong nghiep model HP-500: 15 cai.",
                "1.2. Day chuyen dong goi tu dong XK-200: 2 bo.",
            ],
        },
        {
            "heading": "Dieu 2. Gia ca va thanh toan",
            "paragraphs": [
                "2.1. Don gia may bom: 50.000.000 VND/cai.",
                "2.2. Don gia day chuyen dong goi: 800.000.000 VND/bo.",
                "2.3. Tong gia tri: 2.350.000.000 VND.",
                "2.4. Thanh toan bang VND hoac USD theo ty gia ngan hang tai ngay thanh toan.",
            ],
        },
        {
            "heading": "Dieu 4. Giao hang va lap dat",
            "paragraphs": [
                "4.1. Giao hang trong vong 60 ngay ke tu ngay thanh toan.",
                "4.2. Nguoi ban ho tro lap dat mien phi tai cong trinh Ben mua.",
            ],
        },
        {
            "heading": "Dieu 5. Dao tao su dung thiet bi",
            "paragraphs": [
                "5.1. Nguoi ban to chuc 01 khoa dao tao su dung thiet bi trong 2 ngay lam viec.",
                "5.2. Toi da 5 nhan vien cua Ben mua duoc tham gia mien phi.",
                "5.3. Cap chung chi hoan thanh dao tao sau khi ket thuc.",
            ],
        },
    ]
    _create_docx_pair(
        "Hop_dong_F",
        "HOP DONG MUA BAN THIET BI CONG NGHIEP",
        "HOP DONG MUA BAN THIET BI CONG NGHIEP (SUA DOI)",
        header, clauses_v1, clauses_v2,
    )
    _write_ground_truth(
        "Hop_dong_F", "medium",
        "Hop dong thiet bi cong nghiep - tang so luong, doi don vi tien te, xoa chiet khau, them dao tao",
        [
            {"clause_id": "dieu_1", "type": "SUA",
             "description": "So luong may bom tang 10 len 15 cai; tong gia tri tang theo",
             "old_text_hint": "10 cai", "new_text_hint": "15 cai"},
            {"clause_id": "dieu_2", "type": "SUA",
             "description": "Phuong thuc thanh toan mo rong sang USD theo ty gia; tong gia tri thay doi",
             "old_text_hint": "Thanh toan bang VND", "new_text_hint": "Thanh toan bang VND hoac USD"},
            {"clause_id": "dieu_3", "type": "XOA",
             "description": "Xoa hoan toan dieu khoan uu dai va chiet khau"},
            {"clause_id": "dieu_5", "type": "THEM",
             "description": "Them dieu khoan dao tao su dung thiet bi 2 ngay cho nhan vien Ben mua"},
        ],
    )


# ---------------------------------------------------------------------------
# Hop_dong_G  (medium, 3 thay doi) — van chuyen hang hoa
# ---------------------------------------------------------------------------

def _create_hop_dong_g() -> None:
    header = ["So: 11/2024/HDVC", "Can cu Luat Giao thong duong bo 2008;"]
    clauses_v1 = [
        {
            "heading": "Dieu 1. Doi tuong van chuyen",
            "paragraphs": [
                "1.1. Van chuyen hang hoa tong hop tu kho Ha Noi den kho TP.HCM.",
                "1.2. Trong luong toi da moi chuyen: 20 tan.",
            ],
        },
        {
            "heading": "Dieu 2. Phuong tien va tuyen duong",
            "paragraphs": [
                "2.1. Su dung xe tai trong lon, can tai 20 tan tro len.",
                "2.2. Don vi van chuyen tu chon tuyen duong toi uu.",
                "2.3. Thoi gian giao hang: toi da 5 ngay lam viec.",
            ],
        },
        {
            "heading": "Dieu 3. An toan va bao hiem",
            "paragraphs": [
                "3.1. Don vi van chuyen mua bao hiem hang hoa cho moi chuyen hang.",
                "3.2. Muc bao hiem toi thieu bang 110% gia tri lo hang.",
                "3.3. Tai xe phai co kinh nghiem toi thieu 3 nam.",
            ],
        },
        {
            "heading": "Dieu 4. Phi van chuyen",
            "paragraphs": [
                "4.1. Phi van chuyen: 15.000.000 VND/chuyen.",
                "4.2. Phi nien linh dong tuy theo bien dong gia nhien lieu.",
            ],
        },
    ]
    clauses_v2 = [
        {
            "heading": "Dieu 1. Doi tuong van chuyen",
            "paragraphs": [
                "1.1. Van chuyen hang hoa tong hop tu kho Ha Noi den kho TP.HCM.",
                "1.2. Trong luong toi da moi chuyen: 20 tan.",
            ],
        },
        {
            "heading": "Dieu 2. Phuong tien va tuyen duong",
            "paragraphs": [
                "2.1. Su dung xe tai trong lon, can tai 20 tan tro len.",
                "2.2. Don vi van chuyen phai di theo tuyen duong do Ben thue chi dinh.",
                "2.3. Thoi gian giao hang: toi da 5 ngay lam viec.",
            ],
        },
        {
            "heading": "Dieu 3. An toan va bao hiem",
            "paragraphs": [
                "3.1. Tai xe phai co kinh nghiem toi thieu 3 nam.",
                "3.2. Don vi van chuyen mua bao hiem hang hoa cho moi chuyen hang.",
                "3.3. Muc bao hiem toi thieu bang 110% gia tri lo hang.",
            ],
        },
        {
            "heading": "Dieu 4. Phi van chuyen",
            "paragraphs": [
                "4.1. Phi van chuyen: 15.000.000 VND/chuyen.",
                "4.2. Phi nien linh dong tuy theo bien dong gia nhien lieu.",
            ],
        },
        {
            "heading": "Dieu 5. Boi thuong hang hoa hu hong",
            "paragraphs": [
                "5.1. Don vi van chuyen chiu trach nhiem boi thuong 100% gia tri hang hoa hu hong do loi van chuyen.",
                "5.2. Khieu nai phai gui bang van ban trong vong 48 gio ke tu khi nhan hang.",
            ],
        },
    ]
    _create_docx_pair(
        "Hop_dong_G",
        "HOP DONG VAN CHUYEN HANG HOA",
        "HOP DONG VAN CHUYEN HANG HOA (SUA DOI)",
        header, clauses_v1, clauses_v2,
    )
    _write_ground_truth(
        "Hop_dong_G", "medium",
        "Hop dong van chuyen - sua quyen chon tuyen, hoan vi cac khoan bao hiem, them boi thuong",
        [
            {"clause_id": "dieu_2", "type": "SUA",
             "description": "Thay doi quyen chon tuyen: tu 'tu chon toi uu' sang 'theo chi dinh cua Ben thue'",
             "old_text_hint": "tu chon tuyen duong toi uu", "new_text_hint": "tuyen duong do Ben thue chi dinh"},
            {"clause_id": "dieu_3", "type": "SUA",
             "description": "Hoan vi thu tu: dieu kien tai xe len dau, bao hiem xuong sau",
             "old_text_hint": "3.1. Don vi van chuyen mua bao hiem", "new_text_hint": "3.1. Tai xe phai co kinh nghiem"},
            {"clause_id": "dieu_5", "type": "THEM",
             "description": "Them dieu khoan boi thuong 100% khi hang hoa hu hong do loi van chuyen"},
        ],
    )


# ---------------------------------------------------------------------------
# Hop_dong_H  (hard, 5 thay doi) — lien doanh
# ---------------------------------------------------------------------------

def _create_hop_dong_h() -> None:
    header = ["So: 02/2024/HDLD", "Can cu Luat Doanh nghiep 2020;"]
    clauses_v1 = [
        {
            "heading": "Dieu 1. Muc dich hop tac",
            "paragraphs": [
                "1.1. Hai ben cung hop tac nghien cuu va phat trien san pham cong nghe.",
                "1.2. Thi truong muc tieu: Viet Nam va Dong Nam A.",
            ],
        },
        {
            "heading": "Dieu 2. Von gop",
            "paragraphs": [
                "2.1. Ben A gop 60% von (6.000.000.000 VND).",
                "2.2. Ben B gop 40% von (4.000.000.000 VND) bang tai san va cong nghe.",
            ],
        },
        {
            "heading": "Dieu 3. Dieu kien cham dut",
            "paragraphs": [
                "3.1. Mot trong hai ben co the de nghi cham dut sau 3 nam.",
                "3.2. Thong bao truoc 90 ngay bang van ban.",
            ],
        },
        {
            "heading": "Dieu 4. Phan chia loi nhuan",
            "paragraphs": [
                "4.1. Loi nhuan phan chia theo ty le von gop.",
                "4.2. Chia loi nhuan hang nam sau khi kiem toan.",
            ],
        },
        {
            "heading": "Dieu 5. Thanh ly tai san cu",
            "paragraphs": [
                "5.1. Truoc khi gop von, hai ben thanh ly toan bo tai san cu lien quan.",
                "5.2. Chi phi thanh ly chia deu theo ty le 50/50.",
            ],
        },
    ]
    clauses_v2 = [
        {
            "heading": "Dieu 1. Muc dich hop tac",
            "paragraphs": [
                "1.1. Hai ben cung hop tac nghien cuu va phat trien san pham cong nghe.",
                "1.2. Thi truong muc tieu: Viet Nam va Dong Nam A.",
                "1.3. Cac linh vuc hop tac uu tien: tri tue nhan tao, phan tich du lieu lon va giai phap luu tru dam may.",
                "1.4. Cac ben cam ket dau tu nhan luc chuyen mon trong linh vuc ky thuat phan mem va nghien cuu ung dung.",
                "1.5. Chien luoc phat trien san pham tuan thu Khung Phat trien Ben vung cua Lien hop quoc (SDGs).",
            ],
        },
        {
            "heading": "Dieu 2. Von gop",
            "paragraphs": [
                "2.1. Ben A gop 60% von (6.000.000.000 VND).",
                "2.2. Ben B gop 40% von (4.000.000.000 VND) bang tai san va cong nghe.",
            ],
        },
        {
            "heading": "Dieu 3. Dieu kien cham dut",
            "paragraphs": [
                "3.1. Mot trong hai ben co the de nghi cham dut sau 3 nam.",
                "3.2. Thong bao truoc 90 ngay bang van ban.",
                "3.3. Truong hop vi pham nghiem trong nghia vu tai chinh (cham dong gop von qua 180 ngay), ben kia co quyen cham dut ngay lap tuc.",
                "3.4. Truong hop mot ben lam vao tinh trang pha san hoac bi thu hoi giay phep kinh doanh, hop dong cham dut tu dong.",
                "3.5. Viec cham dut khong giai phong nghia vu bao mat va quyen so huu tri tue da phat sinh truoc do.",
            ],
        },
        {
            "heading": "Dieu 4. Phan chia loi nhuan",
            "paragraphs": [
                "4.1. Loi nhuan phan chia theo ty le von gop.",
                "4.2. Chia loi nhuan hang nam sau khi kiem toan.",
            ],
        },
        {
            "heading": "Dieu 4b. Chia se tai san khi giai the",
            "paragraphs": [
                "4b.1. Khi giai the, tai san duoc phan chia theo thu tu: no vay ngan hang, no nha cung cap, phan von goc, loi nhuan con lai.",
                "4b.2. Tai san vo hinh (thuong hieu, cong nghe doc quyen) duoc dinh gia doc lap truoc khi phan chia.",
            ],
        },
        {
            "heading": "Dieu 5b. Quyen uu tien mua lai co phan",
            "paragraphs": [
                "5b.1. Khi mot ben muon chuyen nhuong co phan, ben kia co quyen uu tien mua lai theo gia thi truong.",
                "5b.2. Thong bao y dinh chuyen nhuong truoc 60 ngay; ben kia co 30 ngay de quyet dinh.",
                "5b.3. Neu ben kia tu choi, co phan moi duoc chuyen nhuong cho ben thu ba voi gia khong thap hon gia chao ban.",
            ],
        },
    ]
    _create_docx_pair(
        "Hop_dong_H",
        "HOP DONG LIEN DOANH",
        "HOP DONG LIEN DOANH (SUA DOI)",
        header, clauses_v1, clauses_v2,
    )
    _write_ground_truth(
        "Hop_dong_H", "hard",
        "Hop dong lien doanh - mo rong muc dich (them 3 doan), bao sung dieu kien cham dut (them 3 doan), "
        "them chia se tai san, them quyen uu tien mua lai, xoa thanh ly tai san cu",
        [
            {"clause_id": "dieu_1", "type": "SUA",
             "description": "Them 3 khoan moi mo rong muc dich hop tac (linh vuc AI, nhan luc, SDGs)",
             "old_text_hint": "Thi truong muc tieu: Viet Nam va Dong Nam A.",
             "new_text_hint": "tri tue nhan tao, phan tich du lieu lon"},
            {"clause_id": "dieu_3", "type": "SUA",
             "description": "Them 3 khoan moi ve cac truong hop cham dut dac biet (vi pham tai chinh, pha san, bao mat)",
             "old_text_hint": "Thong bao truoc 90 ngay",
             "new_text_hint": "cham dong gop von qua 180 ngay"},
            {"clause_id": "dieu_4b", "type": "THEM",
             "description": "Them moi dieu khoan chia se tai san khi giai the (thu tu uu tien, tai san vo hinh)"},
            {"clause_id": "dieu_5b", "type": "THEM",
             "description": "Them moi dieu khoan quyen uu tien mua lai co phan khi chuyen nhuong"},
            {"clause_id": "dieu_5", "type": "XOA",
             "description": "Xoa hoan toan dieu khoan thanh ly tai san cu truoc khi gop von"},
        ],
    )


# ---------------------------------------------------------------------------
# Hop_dong_I  (hard, 4 thay doi) — chuyen giao cong nghe
# Kho: thay doi ngu nghia, tu ngu gan giong nhau
# ---------------------------------------------------------------------------

def _create_hop_dong_i() -> None:
    header = ["So: 06/2024/HDCGCN", "Can cu Luat Chuyen giao cong nghe 2017;"]
    clauses_v1 = [
        {
            "heading": "Dieu 1. Doi tuong chuyen giao",
            "paragraphs": [
                "1.1. Cong nghe san xuat san pham nhua ky thuat cao, bao gom quy trinh va cong thuc.",
                "1.2. Tai lieu cong nghe: ban ve, so do, huong dan ky thuat bang tieng Anh.",
            ],
        },
        {
            "heading": "Dieu 2. Phi chuyen nhuong",
            "paragraphs": [
                "2.1. Phi chuyen nhuong mot lan: 5.000.000.000 VND.",
                "2.2. Thanh toan trong vong 30 ngay sau khi ban giao tai lieu.",
            ],
        },
        {
            "heading": "Dieu 3. Dieu chinh phi",
            "paragraphs": [
                "3.1. Phi duoc dieu chinh hang nam dua tren bien dong gia ca.",
                "3.2. Muc dieu chinh toi da 5% moi nam.",
            ],
        },
        {
            "heading": "Dieu 4. Pham vi su dung",
            "paragraphs": [
                "4.1. Ben nhan duoc phep san xuat tai Viet Nam.",
                "4.2. Khong duoc chuyen nhuong lai cong nghe cho ben thu ba.",
            ],
        },
    ]
    clauses_v2 = [
        {
            "heading": "Dieu 1. Doi tuong chuyen giao",
            "paragraphs": [
                "1.1. Cong nghe san xuat va quy trinh ky thuat san pham nhua ky thuat cao, bao gom quy trinh, cong thuc va thong so van hanh.",
                "1.2. Tai lieu cong nghe: ban ve, so do, huong dan ky thuat bang tieng Anh.",
            ],
        },
        {
            "heading": "Dieu 2. Phi li-xang",
            "paragraphs": [
                "2.1. Phi li-xang mot lan: 5.000.000.000 VND.",
                "2.2. Thanh toan trong vong 30 ngay sau khi ban giao tai lieu.",
            ],
        },
        {
            "heading": "Dieu 3. Dieu chinh phi",
            "paragraphs": [
                "3.1. Phi duoc dieu chinh hang nam dua tren chi so gia tieu dung (CPI) do Tong cuc Thong ke cong bo.",
                "3.2. Muc dieu chinh toi da 5% moi nam.",
            ],
        },
        {
            "heading": "Dieu 4. Pham vi su dung",
            "paragraphs": [
                "4.1. Ben nhan duoc phep san xuat tai Viet Nam va cac nuoc ASEAN co van phong dai dien cua Ben nhan.",
                "4.2. Khong duoc chuyen nhuong lai cong nghe cho ben thu ba.",
                "4.3. San luong san xuat toi da 500 tan/nam; vuot nguong phai dam phan bo sung phi.",
            ],
        },
    ]
    _create_docx_pair(
        "Hop_dong_I",
        "HOP DONG CHUYEN GIAO CONG NGHE",
        "HOP DONG CHUYEN GIAO CONG NGHE (SUA DOI)",
        header, clauses_v1, clauses_v2,
    )
    _write_ground_truth(
        "Hop_dong_I", "hard",
        "Hop dong CGCN - thay doi tu ngu gan giong (phi chuyen nhuong->li-xang, CPI), mo rong pham vi su dung",
        [
            {"clause_id": "dieu_1", "type": "SUA",
             "description": "Bo sung 'quy trinh ky thuat' va 'thong so van hanh' - tu ngu mo rong nhung nghe tuong tu",
             "old_text_hint": "Cong nghe san xuat san pham nhua",
             "new_text_hint": "Cong nghe san xuat va quy trinh ky thuat san pham nhua"},
            {"clause_id": "dieu_2", "type": "SUA",
             "description": "Doi ten 'Phi chuyen nhuong' thanh 'Phi li-xang' - khac ten nhung so tien giu nguyen",
             "old_text_hint": "Phi chuyen nhuong", "new_text_hint": "Phi li-xang"},
            {"clause_id": "dieu_3", "type": "SUA",
             "description": "Thay 'bien dong gia ca' bang 'chi so gia tieu dung (CPI)' - cu the hoa tieu chi dieu chinh",
             "old_text_hint": "bien dong gia ca", "new_text_hint": "chi so gia tieu dung (CPI)"},
            {"clause_id": "dieu_4", "type": "SUA",
             "description": "Mo rong vung pham vi sang ASEAN; them gioi han san luong 500 tan/nam",
             "old_text_hint": "san xuat tai Viet Nam", "new_text_hint": "san xuat tai Viet Nam va cac nuoc ASEAN"},
        ],
    )


# ---------------------------------------------------------------------------
# Hop_dong_J  (hard, 6 thay doi) — hop tac nghien cuu
# ---------------------------------------------------------------------------

def _create_hop_dong_j() -> None:
    header = ["So: 14/2024/HDNC", "Can cu Luat Khoa hoc va Cong nghe 2013;"]
    clauses_v1 = [
        {
            "heading": "Dieu 1. Muc tieu nghien cuu",
            "paragraphs": [
                "1.1. Nghien cuu ung dung tri tue nhan tao trong chan doan y te.",
                "1.2. San pham du kien: mo hinh AI phat hien som ung thu tu anh X-quang.",
            ],
        },
        {
            "heading": "Dieu 2. Ngan sach va nguon tai chinh",
            "paragraphs": [
                "2.1. Tong ngan sach: 10.000.000.000 VND.",
                "2.2. Ben A tai tro 70% (7.000.000.000 VND), Ben B tai tro 30% (3.000.000.000 VND).",
                "2.3. Giai ngan theo tung giai doan sau khi nghiem thu.",
            ],
        },
        {
            "heading": "Dieu 3. Tien do va nghiem thu",
            "paragraphs": [
                "3.1. Giai doan 1 (6 thang): xay dung co so du lieu.",
                "3.2. Giai doan 2 (12 thang): huan luyen va kiem thu mo hinh.",
                "3.3. Nghiem thu cuoi: Hoi dong khoa hoc 5 thanh vien.",
            ],
        },
        {
            "heading": "Dieu 4. Quyen so huu ket qua",
            "paragraphs": [
                "4.1. Ket qua nghien cuu thuoc so huu chung theo ty le tai tro.",
                "4.2. Moi ben duoc su dung ket qua cho muc dich noi bo.",
            ],
        },
        {
            "heading": "Dieu 5. Tham quan co so nghien cuu",
            "paragraphs": [
                "5.1. Cac ben duoc phep tham quan co so nghien cuu cua nhau moi quy mot lan.",
                "5.2. Thong bao truoc 5 ngay lam viec.",
            ],
        },
    ]
    clauses_v2 = [
        {
            "heading": "Dieu 1. Muc tieu nghien cuu",
            "paragraphs": [
                "1.1. Nghien cuu ung dung tri tue nhan tao trong chan doan y te.",
                "1.2. San pham du kien: mo hinh AI phat hien som ung thu tu anh X-quang.",
            ],
        },
        {
            "heading": "Dieu 2. Ngan sach va nguon tai chinh",
            "paragraphs": [
                "2.1. Tong ngan sach: 12.000.000.000 VND.",
                "2.2. Ben A tai tro 60% (7.200.000.000 VND), Ben B tai tro 40% (4.800.000.000 VND).",
                "2.3. Giai ngan theo tung giai doan sau khi nghiem thu.",
            ],
        },
        {
            "heading": "Dieu 3. Tien do va nghiem thu",
            "paragraphs": [
                "3.1. Giai doan 1 (6 thang): xay dung co so du lieu va kiem chung nguon du lieu.",
                "3.2. Giai doan 2 (12 thang): huan luyen va kiem thu mo hinh voi do chinh xac toi thieu 90%.",
                "3.3. Nghiem thu cuoi: Hoi dong khoa hoc 7 thanh vien bao gom 2 chuyen gia quoc te.",
            ],
        },
        {
            "heading": "Dieu 4. Quyen so huu ket qua",
            "paragraphs": [
                "4.1. Ket qua nghien cuu thuoc so huu cua Ben A, Ben B duoc cap quyen su dung doc quyen trong 5 nam.",
                "4.2. Sau 5 nam, ket qua chuyen sang so huu chung theo ty le tai tro hien tai.",
                "4.3. Moi cai tien phat sinh tu ket qua nghien cuu thuoc so huu ben cai tien.",
            ],
        },
        {
            "heading": "Dieu 5. Quyen su dung ket qua nghien cuu",
            "paragraphs": [
                "5.1. Ben B duoc cap li-xang doc quyen su dung ket qua tai thi truong Dong Nam A trong 5 nam.",
                "5.2. Phi li-xang: 500.000.000 VND/nam thanh toan vao dau moi nam.",
                "5.3. Ben A giu quyen su dung tai cac thi truong khac va quyen nghien cuu tiep noi.",
            ],
        },
        {
            "heading": "Dieu 6. Tra thu lao cong bo khoa hoc",
            "paragraphs": [
                "6.1. Moi bai bao dang tren tap chi quoc te Q1/Q2 duoc thuong 50.000.000 VND.",
                "6.2. Bang sang che duoc cap tai Viet Nam hoac quoc te: 200.000.000 VND.",
                "6.3. Kinh phi thuong trich tu quy nghien cuu chung.",
            ],
        },
    ]
    _create_docx_pair(
        "Hop_dong_J",
        "HOP DONG HOP TAC NGHIEN CUU",
        "HOP DONG HOP TAC NGHIEN CUU (SUA DOI)",
        header, clauses_v1, clauses_v2,
    )
    _write_ground_truth(
        "Hop_dong_J", "hard",
        "Hop dong nghien cuu - thay doi ngan sach/co cau tai tro, them dieu kien nghiem thu, "
        "dao nguoc quyen so huu, them quyen su dung va tra thuong KH",
        [
            {"clause_id": "dieu_2", "type": "SUA",
             "description": "Tong ngan sach tang 10 ti len 12 ti; co cau tai tro thay doi (70/30 -> 60/40)",
             "old_text_hint": "10.000.000.000", "new_text_hint": "12.000.000.000"},
            {"clause_id": "dieu_3", "type": "SUA",
             "description": "Them dieu kien kiem chung du lieu; them nguong chinh xac 90%; tang hoi dong len 7 nguoi co 2 chuyen gia quoc te",
             "old_text_hint": "Hoi dong khoa hoc 5 thanh vien", "new_text_hint": "7 thanh vien bao gom 2 chuyen gia quoc te"},
            {"clause_id": "dieu_4", "type": "SUA",
             "description": "Dao nguoc quyen so huu: tu 'so huu chung theo ty le' sang 'so huu cua Ben A, Ben B duoc li-xang 5 nam'",
             "old_text_hint": "so huu chung theo ty le tai tro", "new_text_hint": "so huu cua Ben A, Ben B duoc cap quyen su dung"},
            {"clause_id": "dieu_5", "type": "SUA",
             "description": "Noi dung Dieu 5 thay doi hoan toan: tu 'tham quan co so' sang 'quyen su dung ket qua nghien cuu'",
             "old_text_hint": "tham quan co so nghien cuu", "new_text_hint": "li-xang doc quyen su dung ket qua"},
            {"clause_id": "dieu_6", "type": "THEM",
             "description": "Them moi dieu khoan tra thuong khi cong bo bai bao Q1/Q2 va bang sang che"},
            {"clause_id": "dieu_5_cu", "type": "XOA",
             "description": "Xoa noi dung cu cua Dieu 5 ve quyen tham quan co so nghien cuu"},
        ],
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def generate_all_pairs() -> None:
    """Sinh tat ca 10 cap hop dong mau va file ground truth tuong ung."""
    print("=" * 60)
    print("TAO TAP DU LIEU MAU (10 CAP HOP DONG)")
    print("=" * 60)

    _create_hop_dong_a()
    _create_hop_dong_b()
    _create_hop_dong_c()
    _create_hop_dong_d()
    _create_hop_dong_e()
    _create_hop_dong_f()
    _create_hop_dong_g()
    _create_hop_dong_h()
    _create_hop_dong_i()
    _create_hop_dong_j()

    print("\n" + "=" * 60)
    print(f"Hoan thanh: 10 cap DOCX trong {RAW_DIR}")
    print(f"Ground truth: 10 file JSON trong {GT_DIR}")
    print("=" * 60)


def main() -> None:
    generate_all_pairs()


if __name__ == "__main__":
    main()
