# 🚀 Payment Gateway API

A robust RESTful Payment Gateway API built with Django REST Framework, designed for Small and Medium Enterprises (SMEs) to accept payments via Paystack integration.

## ✨ Features

- **RESTful API** with versioning (`/api/v1/`)
- **Paystack Integration** for secure payment processing
- **Comprehensive Testing** with 80%+ coverage
- **CI/CD Pipeline** with GitHub Actions
- **Docker Support** for containerization
- **Security Scanning** with automated vulnerability checks
- **Performance Testing** with Locust
- **Production Ready** with PostgreSQL and Gunicorn

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   API Layer     │    │  Service Layer  │    │  Data Layer     │
│   (Views)       │◄──►│   (Business     │◄──►│   (Models)      │
│                 │    │    Logic)       │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Serializers   │    │  Paystack API   │    │   Database      │
│   (Validation)  │    │  Integration    │    │   (PostgreSQL)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL (for production)
- Paystack Account and API Keys

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd InternPulsePaymentApi
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your Paystack API keys
   ```

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Start development server**
   ```bash
   python manage.py runserver
   ```

### Docker Development

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f web

# Stop services
docker-compose down
```

## 📚 API Documentation

### Base URL
```
http://localhost:8000/api/v1/
```

### Endpoints

#### 1. Create Payment
```http
POST /api/v1/payments/
```

**Request Body:**
```json
{
  "customer_name": "John Doe",
  "customer_email": "john@example.com",
  "phone_number": "1234567890",
  "state": "Lagos",
  "country": "Nigeria",
  "amount": "50.00",
  "currency": "NGN"
}
```

**Response:**
```json
{
  "status": "success",
  "payment": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "customer_name": "John Doe",
    "customer_email": "john@example.com",
    "amount": "50.00",
    "currency": "NGN",
    "status": "pending",
    "paystack_authorization_url": "https://checkout.paystack.com/abc123"
  },
  "message": "Payment created successfully"
}
```

#### 2. Get Payment Status
```http
GET /api/v1/payments/{payment_id}/
```

**Response:**
```json
{
  "status": "success",
  "payment": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "customer_name": "John Doe",
    "customer_email": "john@example.com",
    "amount": "50.00",
    "currency": "NGN",
    "status": "completed",
    "created_at": "2024-01-01T00:00:00Z"
  },
  "message": "Payment details retrieved successfully"
}
```

#### 3. Paystack Webhook
```http
POST /api/v1/payments/webhook/paystack/
```

**Request Body:**
```json
{
  "event": "charge.success",
  "data": {
    "reference": "PAY-ABC123",
    "status": "success",
    "amount": 5000,
    "id": 123456789
  }
}
```

## 🧪 Testing

### Run Tests
```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=payments --cov-report=html

# Run specific test file
python -m pytest payments/tests/test_views.py -v
```

### Test Coverage
- **Models**: 25 tests ✅
- **Services**: 20 tests ✅
- **Views**: 21 tests ✅
- **Total**: 66 tests with 80%+ coverage ✅

### Performance Testing
```bash
# Install Locust
pip install locust

# Run performance tests
locust -f performance_tests/locustfile.py --host=http://localhost:8000
```

## 🔒 Security

### Security Features
- **Input Validation** with Django serializers
- **SQL Injection Protection** with Django ORM
- **XSS Protection** with Django's built-in security
- **CSRF Protection** for webhook endpoints
- **Environment Variable Management** for sensitive data

### Security Scanning
The CI/CD pipeline includes:
- **Bandit** for Python security analysis
- **Safety** for dependency vulnerability scanning
- **pip-audit** for package security checks

## 🚀 Deployment

### Render Deployment

1. **Connect to Render**
   - Link your GitHub repository
   - Configure environment variables
   - Set build command: `pip install -r requirements.txt`
   - Set start command: `gunicorn payment_api.wsgi:application`

2. **Environment Variables**
   ```
   DEBUG=False
   DATABASE_URL=<postgresql-url>
   PAYSTACK_SECRET_KEY=<your-secret-key>
   PAYSTACK_PUBLIC_KEY=<your-public-key>
   PAYSTACK_BASE_URL=https://api.paystack.co
   BASE_URL=https://your-app.onrender.com
   ```

### Docker Deployment

```bash
# Build image
docker build -t payment-gateway-api .

# Run container
docker run -p 8000:8000 -e DATABASE_URL=<url> payment-gateway-api
```

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow

The CI/CD pipeline includes:

1. **Testing**
   - Unit tests with pytest
   - Coverage reporting
   - Multiple Python versions

2. **Code Quality**
   - Linting with flake8
   - Code formatting with black
   - Type checking with mypy

3. **Security**
   - Vulnerability scanning
   - Dependency analysis
   - Security reports

4. **Deployment**
   - Automatic deployment to Render
   - Docker image building
   - Health checks

5. **Performance**
   - Load testing with Locust
   - Performance monitoring

## 📊 Monitoring

### Health Check Endpoint
```http
GET /api/v1/payments/
```

### Logging
- Application logs in `logs/` directory
- Structured logging for production
- Error tracking and monitoring

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 style guide
- Write tests for new features
- Update documentation
- Ensure 80%+ test coverage

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Check the documentation
- Review the test cases for examples

## 🔗 Links

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Paystack API Documentation](https://paystack.com/docs/)
- [Render Documentation](https://render.com/docs)

---

**Built with ❤️ for SMEs**
