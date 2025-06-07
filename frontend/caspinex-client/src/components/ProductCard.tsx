import React from 'react';
import { Card, Button, Spinner, Badge } from 'react-bootstrap'; // Added Badge

export interface ApiCategory {
  id: number;
  name: string;
  slug: string;
}
export interface ApiProduct {
  id: number | string;
  name: string;
  slug: string;
  price: string;
  image?: string | null;
  description?: string;
  category?: ApiCategory;
  available?: boolean;
  stock?: number;
}

interface ProductCardProps {
  product: ApiProduct;
  onAddToCart: (productId: number | string) => void;
  isAdding?: boolean;
}

const ProductCard: React.FC<ProductCardProps> = ({ product, onAddToCart, isAdding }) => {
  const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://127.0.0.1:8000';
  const imageUrl = product.image ? (product.image.startsWith('http') ? product.image : `${API_BASE_URL}${product.image}`) : "https://via.placeholder.com/300x200.png?text=Caspinex";

  const isProductUnavailable = product.available === false || (typeof product.stock === 'number' && product.stock === 0);

  return (
    <Card className="h-100 shadow-sm product-card"> {/* Added a custom class for potential specific styling */}
      <Card.Img
        variant="top"
        src={imageUrl}
        alt={product.name}
        className="product-card-img" // Custom class for image if needed
        style={{ height: '200px', objectFit: 'contain', paddingTop: '1rem' }} // Added more padding top
      />
      <Card.Body className="d-flex flex-column p-3"> {/* Ensured padding */}
        {product.category && (
          <Badge pill bg="secondary" className="mb-2 align-self-start">{product.category.name}</Badge>
        )}
        <Card.Title
          title={product.name}
          className="product-card-title mb-2" // Custom class for title
          style={{ fontSize: '1rem', fontWeight: 'bold', overflow: 'hidden', textOverflow: 'ellipsis', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', minHeight: '2.4em' }} // Adjusted minHeight
        >
          {product.name}
        </Card.Title>

        <Card.Text className="mb-3 product-card-price" style={{ fontSize: '1.1rem', fontWeight: '600', color: '#333' }}>
          {parseFloat(product.price).toLocaleString()} تومان
        </Card.Text>

        <Button
          variant={isProductUnavailable ? "outline-secondary" : "primary"} // Changed unavailable variant
          className="mt-auto w-100" // Ensure button takes full width of its container if desired
          onClick={() => onAddToCart(product.id)}
          disabled={isProductUnavailable || isAdding}
          size="sm" // Smaller button
        >
          {isAdding ? (
            <>
              <Spinner as="span" animation="border" size="sm" role="status" aria-hidden="true" />
              {' '}در حال افزودن...
            </>
          ) : isProductUnavailable ? "ناموجود" : "افزودن به سبد"}
        </Button>
      </Card.Body>
    </Card>
  );
};

export default ProductCard;
