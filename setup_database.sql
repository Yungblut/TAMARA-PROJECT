-- ===========================================
-- TAMARA Database Setup Script
-- ===========================================
-- Ejecutar como root en MariaDB:
--   mysql -u root -p < setup_database.sql
-- ===========================================

-- 1. Crear la base de datos
CREATE DATABASE IF NOT EXISTS tamara_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

-- 2. Crear usuario con password (CAMBIA 'tu_password_seguro')
CREATE USER IF NOT EXISTS 'tamara_user'@'localhost' 
    IDENTIFIED BY 'tu_password_seguro';

-- 3. Dar permisos de SOLO LECTURA
GRANT SELECT ON tamara_db.* TO 'tamara_user'@'localhost';
FLUSH PRIVILEGES;

-- 4. Usar la base de datos
USE tamara_db;

-- ===========================================
-- TABLAS DE EJEMPLO
-- ===========================================

-- Tabla: usuarios
CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    rol ENUM('admin', 'usuario', 'invitado') DEFAULT 'usuario',
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla: productos
CREATE TABLE IF NOT EXISTS productos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(200) NOT NULL,
    descripcion TEXT,
    precio DECIMAL(10, 2) NOT NULL,
    stock INT DEFAULT 0,
    categoria VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla: pedidos
CREATE TABLE IF NOT EXISTS pedidos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    total DECIMAL(10, 2) NOT NULL,
    estado ENUM('pendiente', 'procesando', 'enviado', 'entregado', 'cancelado') DEFAULT 'pendiente',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

-- Tabla: detalle_pedidos
CREATE TABLE IF NOT EXISTS detalle_pedidos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    pedido_id INT NOT NULL,
    producto_id INT NOT NULL,
    cantidad INT NOT NULL,
    precio_unitario DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (pedido_id) REFERENCES pedidos(id),
    FOREIGN KEY (producto_id) REFERENCES productos(id)
);

-- ===========================================
-- DATOS DE EJEMPLO
-- ===========================================

-- Usuarios de ejemplo
INSERT INTO usuarios (nombre, email, rol, activo) VALUES
    ('Ana García', 'ana@ejemplo.com', 'admin', TRUE),
    ('Carlos López', 'carlos@ejemplo.com', 'usuario', TRUE),
    ('María Rodríguez', 'maria@ejemplo.com', 'usuario', TRUE),
    ('Pedro Martínez', 'pedro@ejemplo.com', 'usuario', FALSE),
    ('Laura Fernández', 'laura@ejemplo.com', 'invitado', TRUE),
    ('Diego Sánchez', 'diego@ejemplo.com', 'usuario', TRUE),
    ('Sofía Torres', 'sofia@ejemplo.com', 'usuario', TRUE),
    ('Miguel Ruiz', 'miguel@ejemplo.com', 'admin', TRUE),
    ('Lucía Morales', 'lucia@ejemplo.com', 'usuario', TRUE),
    ('Andrés Díaz', 'andres@ejemplo.com', 'invitado', TRUE);

-- Productos de ejemplo
INSERT INTO productos (nombre, descripcion, precio, stock, categoria) VALUES
    ('Laptop HP Pavilion', 'Laptop 15.6" Intel Core i5, 8GB RAM', 899.99, 15, 'Electrónica'),
    ('Mouse Logitech MX', 'Mouse inalámbrico ergonómico', 79.99, 50, 'Accesorios'),
    ('Teclado Mecánico RGB', 'Teclado gaming con switches Cherry MX', 129.99, 30, 'Accesorios'),
    ('Monitor Samsung 27"', 'Monitor 4K UHD con HDR', 449.99, 20, 'Electrónica'),
    ('Webcam HD 1080p', 'Cámara web con micrófono integrado', 59.99, 45, 'Accesorios'),
    ('Auriculares Sony WH', 'Auriculares Bluetooth con ANC', 299.99, 25, 'Audio'),
    ('Parlante JBL Flip', 'Parlante Bluetooth portátil', 99.99, 40, 'Audio'),
    ('Cable USB-C 2m', 'Cable de carga rápida', 14.99, 100, 'Cables'),
    ('Hub USB 7 puertos', 'Hub USB 3.0 con alimentación', 34.99, 35, 'Accesorios'),
    ('Mousepad XL Gaming', 'Mousepad extendido 90x40cm', 24.99, 60, 'Accesorios');

-- Pedidos de ejemplo
INSERT INTO pedidos (usuario_id, total, estado) VALUES
    (1, 979.98, 'entregado'),
    (2, 129.99, 'enviado'),
    (3, 549.98, 'procesando'),
    (4, 79.99, 'cancelado'),
    (5, 399.98, 'pendiente'),
    (6, 1349.97, 'entregado'),
    (7, 59.99, 'enviado'),
    (2, 164.98, 'pendiente');

-- Detalle de pedidos
INSERT INTO detalle_pedidos (pedido_id, producto_id, cantidad, precio_unitario) VALUES
    (1, 1, 1, 899.99),
    (1, 2, 1, 79.99),
    (2, 3, 1, 129.99),
    (3, 4, 1, 449.99),
    (3, 5, 1, 59.99),
    (3, 8, 2, 14.99),
    (4, 2, 1, 79.99),
    (5, 6, 1, 299.99),
    (5, 7, 1, 99.99),
    (6, 1, 1, 899.99),
    (6, 4, 1, 449.99),
    (7, 5, 1, 59.99),
    (8, 3, 1, 129.99),
    (8, 9, 1, 34.99);

-- ===========================================
-- VERIFICACIÓN
-- ===========================================
SELECT 'Tablas creadas:' AS mensaje;
SHOW TABLES;

SELECT 'Conteo de registros:' AS mensaje;
SELECT 
    (SELECT COUNT(*) FROM usuarios) AS usuarios,
    (SELECT COUNT(*) FROM productos) AS productos,
    (SELECT COUNT(*) FROM pedidos) AS pedidos,
    (SELECT COUNT(*) FROM detalle_pedidos) AS detalles;

-- ===========================================
-- ¡LISTO! Ahora puedes probar con TAMARA:
-- "¿Cuántos usuarios hay?"
-- "¿Qué productos tienen stock mayor a 30?"
-- "¿Cuáles son los pedidos pendientes?"
-- ===========================================
