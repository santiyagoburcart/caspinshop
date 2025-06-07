import React, { useState, useEffect, useCallback } from 'react';
import { Container, Row, Col, Spinner, Alert, Button, Form, Pagination, Card, Badge } from 'react-bootstrap'; // Added Card, Badge
import axios from 'axios';
import ProductCard, { ApiProduct } from '../../components/ProductCard';

interface PaginatedProductResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: ApiProduct[];
}

interface CartApiResponse {
  id: string;
  items: Array<{
    id: number;
    product_detail: { id: number | string; name: string };
    quantity: number;
    subtotal: string;
  }>;
  total_items: number;
  total_price: string;
}

const ProductListPage: React.FC = () => {
  const [products, setProducts] = useState<ApiProduct[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [addingProductId, setAddingProductId] = useState<number | string | null>(null);
  const [addToCartError, setAddToCartError] = useState<string | null>(null);
  const [cartItemCount, setCartItemCount] = useState<number>(0);

  const [searchTerm, setSearchTerm] = useState<string>('');
  const [categoryFilter, setCategoryFilter] = useState<string>('');
  const [ordering, setOrdering] = useState<string>('');

  const [currentPage, setCurrentPage] = useState<number>(1);
  const [totalProductsCount, setTotalProductsCount] = useState<number>(0);
  const [nextPageUrl, setNextPageUrl] = useState<string | null>(null);
  const [previousPageUrl, setPreviousPageUrl] = useState<string | null>(null);
  const ITEMS_PER_PAGE = 10; // This is just for client-side calculation of totalPages. Actual items per page is set by backend.

  const API_PRODUCTS_URL = process.env.REACT_APP_API_SHOP_URL || '/api/v1/shop/products/';
  const API_CART_URL = process.env.REACT_APP_API_CART_URL || '/api/v1/shop/cart/mine/';

  const fetchProducts = useCallback(async (pageToFetch: number, isFilterOrOrderChange: boolean = false) => {
    if (isFilterOrOrderChange) { // If filters changed, always fetch page 1
        pageToFetch = 1;
        // We also need to ensure currentPage state is updated to 1 if filters change
        // This will be handled by the useEffect that calls this.
    }
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string | number> = { page: pageToFetch };
      if (searchTerm.trim()) params.name = searchTerm.trim();
      if (categoryFilter.trim()) params.category_name = categoryFilter.trim();
      if (ordering) params.ordering = ordering;

      const response = await axios.get<PaginatedProductResponse>(API_PRODUCTS_URL, { params });
      setProducts(response.data.results);
      setTotalProductsCount(response.data.count);
      setNextPageUrl(response.data.next);
      setPreviousPageUrl(response.data.previous);
      setCurrentPage(pageToFetch); // Update current page based on what was fetched
    } catch (err) {
      if (axios.isAxiosError(err)) {
        setError(err.response?.data?.detail || err.message || 'خطایی در دریافت محصولات رخ داد.');
      } else {
        setError('یک خطای ناشناخته رخ داد.');
      }
      console.error("Error fetching products:", err);
      setProducts([]);
      setTotalProductsCount(0);
      setNextPageUrl(null);
      setPreviousPageUrl(null);
    } finally {
      setLoading(false);
    }
  }, [API_PRODUCTS_URL, searchTerm, categoryFilter, ordering]); // Removed currentPage from here

  // Effect for filter/ordering changes
  useEffect(() => {
    // When searchTerm, categoryFilter, or ordering change, reset to page 1 and fetch.
    // The fetchProducts function will be called with page 1.
    // We also need to set currentPage state to 1.
    if (currentPage !== 1) { // Only reset if not already on page 1 to avoid loop with next effect
        setCurrentPage(1);
    }
    const timerId = setTimeout(() => {
        fetchProducts(1, true); // Pass true to indicate it's a filter/order change
    }, 500);
    return () => clearTimeout(timerId);
  }, [searchTerm, categoryFilter, ordering]); // Removed fetchProducts from here

  // Effect for direct page changes (e.g., from pagination controls)
  useEffect(() => {
    // This effect runs when currentPage changes due to pagination controls
    // or due to the filter/order effect setting it to 1.
    fetchProducts(currentPage);
  }, [currentPage, fetchProducts]); // fetchProducts is now a dependency here.

  useEffect(() => {
    const fetchInitialCart = async () => {
      try {
        const response = await axios.get<CartApiResponse>(API_CART_URL);
        setCartItemCount(response.data.total_items || 0);
      } catch (err) { console.warn("Could not fetch initial cart:", err); }
    };
    fetchInitialCart();
  }, [API_CART_URL]);

  const handleAddToCart = async (productId: number | string) => {
    setAddingProductId(productId);
    setAddToCartError(null);
    try {
      const addItemUrl = (process.env.REACT_APP_API_CART_URL || '/api/v1/shop/cart/') + 'add-item/';
      const response = await axios.post<CartApiResponse>(addItemUrl, { product_id: productId, quantity: 1 });
      alert(`محصول با شناسه ${productId} با موفقیت به سبد خرید اضافه شد.`);
      if (response.data && typeof response.data.total_items !== 'undefined') {
        setCartItemCount(response.data.total_items);
      }
    } catch (err) {
      let message = 'خطا در افزودن محصول به سبد خرید.';
      if (axios.isAxiosError(err)) {
        message = err.response?.data?.error || err.response?.data?.detail || err.message || message;
      }
      setAddToCartError(message);
      alert(`خطا: ${message}`);
    } finally {
      setAddingProductId(null);
    }
  };

  const totalPages = Math.ceil(totalProductsCount / ITEMS_PER_PAGE);

  const handlePageChange = (pageNumber: number) => {
    if (pageNumber >= 1 && pageNumber <= totalPages && pageNumber !== currentPage) {
      setCurrentPage(pageNumber);
    }
  };

  const renderPaginationItems = () => {
    if (totalPages <= 1) return null;
    let items = []; const pageWindow = 2;
    items.push(<Pagination.Prev key="prev" disabled={currentPage === 1} onClick={() => handlePageChange(currentPage - 1)} />);
    for (let number = 1; number <= totalPages; number++) {
      if ( number === 1 || number === totalPages || (number >= currentPage - pageWindow && number <= currentPage + pageWindow) ) {
        items.push(<Pagination.Item key={number} active={number === currentPage} onClick={() => handlePageChange(number)}>{number}</Pagination.Item>);
      } else if ( (number === currentPage - pageWindow - 1 && items[items.length-1].key !== 'ellipsis_start') ||
                  (number === currentPage + pageWindow + 1 && items[items.length-1].key !== 'ellipsis_end') ) {
        items.push(<Pagination.Ellipsis key={number === currentPage - pageWindow - 1 ? 'ellipsis_start' : 'ellipsis_end'} disabled />);
      }
    }
    items.push(<Pagination.Next key="next" disabled={currentPage === totalPages} onClick={() => handlePageChange(currentPage + 1)} />);
    return items;
  };

  const orderingOptions = [
    { value: '', label: 'مرتب‌سازی پیش‌فرض' }, { value: 'price', label: 'قیمت: ارزان‌ترین' },
    { value: '-price', label: 'قیمت: گران‌ترین' }, { value: 'name', label: 'نام: الف تا ی' },
    { value: '-name', label: 'نام: ی تا الف' }, { value: '-created_at', label: 'جدیدترین' },
    { value: 'created_at', label: 'قدیمی‌ترین' },
  ];

  return (
    <Container fluid className="py-4 px-md-4">
      <Row className="mb-3 align-items-center">
        <Col xs={12} md> <h2 className="mb-2 mb-md-0">لیست محصولات</h2> </Col>
        <Col xs={12} md="auto"> <p className="text-muted mb-0">تعداد اقلام در سبد: <Badge bg="info" pill>{cartItemCount}</Badge></p> </Col>
      </Row>
      {addToCartError && <Alert variant="danger" onClose={() => setAddToCartError(null)} dismissible className="mb-3">{addToCartError}</Alert>}

      <Card className="mb-4 p-3 shadow-sm">
        <Form>
          <Row className="g-3 align-items-end">
            <Col xs={12} md={6} lg={4}>
              <Form.Group controlId="searchTerm"><Form.Label className="small fw-bold">جستجو در نام محصول</Form.Label>
                <Form.Control type="text" placeholder="مثال: لپ تاپ ..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} size="sm"/>
              </Form.Group>
            </Col>
            <Col xs={12} md={6} lg={4}>
              <Form.Group controlId="categoryFilter"><Form.Label className="small fw-bold">جستجو در دسته‌بندی</Form.Label>
                <Form.Control type="text" placeholder="مثال: الکترونیکی ..." value={categoryFilter} onChange={(e) => setCategoryFilter(e.target.value)} size="sm"/>
              </Form.Group>
            </Col>
            <Col xs={12} md={12} lg={4}>
              <Form.Group controlId="orderingSelect"><Form.Label className="small fw-bold">مرتب‌سازی بر اساس</Form.Label>
                <Form.Select value={ordering} onChange={(e) => setOrdering(e.target.value)} aria-label="Select ordering" size="sm">
                  {orderingOptions.map(opt => (<option key={opt.value} value={opt.value}>{opt.label}</option>))}
                </Form.Select>
              </Form.Group>
            </Col>
          </Row>
        </Form>
      </Card>

      {loading && (<div className="text-center py-5"><Spinner animation="border" variant="primary" role="status" style={{ width: '3rem', height: '3rem' }}><span className="visually-hidden">در حال بارگذاری...</span></Spinner><p className="mt-2 text-muted">در حال دریافت محصولات...</p></div>)}
      {!loading && error && (<Alert variant="danger" className="text-center"><Alert.Heading>خطا!</Alert.Heading><p>{error}</p><Button onClick={() => fetchProducts(1, true)} variant="outline-danger" size="sm">تلاش مجدد</Button></Alert>)}
      {!loading && !error && products.length === 0 && (<Alert variant="info" className="text-center py-4"><p className="mb-0 h5">هیچ محصولی با این مشخصات یافت نشد.</p><p className="small text-muted">لطفاً فیلترهای خود را تغییر دهید یا بعداً دوباره تلاش کنید.</p></Alert>)}

      {!loading && !error && products.length > 0 && (
        <>
          <Row xs={1} sm={2} md={3} lg={4} className="g-4">
            {products.map(product => (
              <Col key={product.id} className="d-flex align-items-stretch">
                <ProductCard product={product} onAddToCart={handleAddToCart} isAdding={addingProductId === product.id} />
              </Col>
            ))}
          </Row>
          {totalPages > 1 && (
            <Row className="mt-4 pt-2"><Col className="d-flex justify-content-center">
                <Pagination size="sm">{renderPaginationItems()}</Pagination>
            </Col></Row>
          )}
        </>
      )}
    </Container>
  );
};

export default ProductListPage;
