def _validate_sale(menu, qty, price):
    if qty <= 0:        return 'qty > 0'
    if price < 0:       return 'price >= 0'
    if qty > 500:       return 'qty too large'
    return None

def log_sale(menu, qty, price):
    err = _validate_sale(menu, qty, price)
    if err: 
        return {'ok': False, 'tool': 'log_sale', 'error': err}
    
    return {'ok': True, 'msg': f'บันทึก {menu} จำนวน {qty} สำเร็จ'}

TOOL_REGISTRY = {
    'log_sale': {
        'fn': log_sale,
        'args': ('menu', 'qty', 'price'),
        'coerce': {'menu': str, 'qty': int, 'price': float}
    }
}