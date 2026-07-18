def _validate_sale(menu, qty, price):
    if qty <= 0:
        return 'qty > 0'
    if price < 0:
        return 'price >= 0'
    if qty > 500:
        return 'qty too large'
    return None


def log_sale(menu, qty, price):
    err = _validate_sale(menu, qty, price)
    if err:
        return {'ok': False, 'tool': 'log_sale', 'error': err}
    return {'ok': True, 'msg': f'บันทึก {menu} จำนวน {qty} สำเร็จ'}


def query_sales(date):
    # ฟังก์ชันจำลองการดูยอดขาย
    return {'ok': True, 'msg': f'ยอดขายวันที่ {date} ทั้งหมด 1,500 บาท'}


def send_alert(message):
    # ฟังก์ชันจำลองการส่งแจ้งเตือน
    return {'ok': True, 'msg': f'ส่งแจ้งเตือนสำเร็จ: "{message}"'}


TOOL_REGISTRY = {
    'log_sale': {
        'fn': log_sale,
        'args': ('menu', 'qty', 'price'),
        'coerce': {'menu': str, 'qty': int, 'price': float}
    },
    'query_sales': {
        'fn': query_sales,
        'args': ('date',),
        'coerce': {'date': str}
    },
    'send_alert': {
        'fn': send_alert,
        'args': ('message',),
        'coerce': {'message': str}
    }
}
