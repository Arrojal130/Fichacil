CREATE TABLE IF NOT EXISTS negocios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre VARCHAR(100) NOT NULL,
    slug VARCHAR(50) NOT NULL UNIQUE,
    direccion VARCHAR(255),
    nif VARCHAR(20),
    lat FLOAT,
    lon FLOAT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_negocios_slug ON negocios (slug);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE,
    dni VARCHAR(20),
    password_hash VARCHAR(255),
    pin_hash VARCHAR(255),
    rol VARCHAR(16) NOT NULL,
    active BOOLEAN NOT NULL DEFAULT 1,
    negocio_id INTEGER NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(negocio_id) REFERENCES negocios(id)
);

CREATE INDEX IF NOT EXISTS ix_users_email ON users (email);
CREATE INDEX IF NOT EXISTS ix_users_negocio_id ON users (negocio_id);

CREATE TABLE IF NOT EXISTS fichajes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo VARCHAR(16) NOT NULL,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    lat FLOAT,
    lon FLOAT,
    distancia_metros FLOAT,
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    empleado_id INTEGER NOT NULL,
    negocio_id INTEGER NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(empleado_id) REFERENCES users(id),
    FOREIGN KEY(negocio_id) REFERENCES negocios(id)
);

CREATE INDEX IF NOT EXISTS ix_fichajes_timestamp ON fichajes (timestamp);
CREATE INDEX IF NOT EXISTS ix_fichajes_empleado_id ON fichajes (empleado_id);
CREATE INDEX IF NOT EXISTS ix_fichajes_negocio_id ON fichajes (negocio_id);

CREATE TABLE IF NOT EXISTS correcciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fichaje_id INTEGER NOT NULL,
    timestamp_original DATETIME NOT NULL,
    timestamp_corregido DATETIME NOT NULL,
    motivo VARCHAR(16) NOT NULL,
    detalle TEXT,
    estado VARCHAR(16) NOT NULL DEFAULT 'pendiente',
    creador_id INTEGER NOT NULL,
    aprobador_id INTEGER,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at DATETIME,
    FOREIGN KEY(fichaje_id) REFERENCES fichajes(id),
    FOREIGN KEY(creador_id) REFERENCES users(id),
    FOREIGN KEY(aprobador_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS ix_correcciones_fichaje_id ON correcciones (fichaje_id);
