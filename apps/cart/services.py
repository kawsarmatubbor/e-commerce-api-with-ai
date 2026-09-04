from apps.product.models import Product


def get_quantity_error(product, quantity):
    if not product.is_active:
        return 'This product is not available.'

    if (
        product.stock_status == Product.StockStatus.OUT_OF_STOCK
        and not product.allow_backorder
    ):
        return 'This product is out of stock.'

    if not product.allow_backorder and quantity > product.stock_quantity:
        return f'Only {product.stock_quantity} item(s) are available.'

    return None

