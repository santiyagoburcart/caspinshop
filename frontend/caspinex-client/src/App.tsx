import React from 'react';
import 'bootstrap/dist/css/bootstrap.min.css';
import { BrowserRouter as Router, Route, Routes, Link } from 'react-router-dom';
import { Container, Navbar, Nav } from 'react-bootstrap';
import ProductListPage from './pages/ProductListPage'; // Import the new page

const HomePage = () => (
  <Container className="mt-4">
    <h2>صفحه اصلی فروشگاه کاسپینکس</h2>
    <p>به فروشگاه ما خوش آمدید! این صفحه اصلی است.</p>
    <p>می‌توانید برای مشاهده محصولات به لینک "محصولات" در نوبار مراجعه کنید.</p>
  </Container>
);
// const ProductsPagePlaceholder = () => <h2>Products Page Placeholder</h2>; // No longer needed
const LoginPage = () => (
  <Container className="mt-4">
    <h2>صفحه ورود / ثبت نام</h2>
    <p>اینجا فرم‌های ورود و ثبت نام قرار خواهند گرفت.</p>
  </Container>
);


function App() {
  return (
    <Router>
      <Navbar bg="dark" variant="dark" expand="lg">
        <Container>
          <Navbar.Brand as={Link} to="/">کاسپینکس</Navbar.Brand>
          <Navbar.Toggle aria-controls="basic-navbar-nav" />
          <Navbar.Collapse id="basic-navbar-nav">
            <Nav className="me-auto">
              <Nav.Link as={Link} to="/">خانه</Nav.Link>
              <Nav.Link as={Link} to="/products">محصولات</Nav.Link> {/* Link to the new ProductListPage */}
            </Nav>
            <Nav>
              <Nav.Link as={Link} to="/login">ورود / ثبت نام</Nav.Link>
              {/* Add Cart link/icon later */}
            </Nav>
          </Navbar.Collapse>
        </Container>
      </Navbar>

      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/products" element={<ProductListPage />} /> {/* Route for ProductListPage */}
        {/* <Route path="/products-placeholder" element={<ProductsPagePlaceholder />} /> */}
        <Route path="/login" element={<LoginPage />} />
        {/* Add other routes here: product detail, cart, checkout, profile etc. */}
      </Routes>
    </Router>
  );
}

export default App;
