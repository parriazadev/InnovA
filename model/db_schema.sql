-- ==========================================
-- ESQUEMA DE BASE DE DATOS - INNOVA RADAR
-- Plataforma: Supabase (PostgreSQL)
-- ==========================================

-- 1. Tabla de Clientes
-- Almacena el perfil y contexto estratégico de las empresas.
create table if not exists clients (
  id bigint primary key generated always as identity,
  name text not null,
  industry text,
  tech_context_raw text, -- Texto extraído (scraping)
  last_updated timestamptz default now()
);

-- 2. Tabla de Tendencias
-- Noticias o papers recolectados desde RSS.
create table if not exists trends (
  id bigint primary key generated always as identity,
  title text not null,
  source text,
  url text unique, -- Evitar duplicados
  summary text,
  published_at timestamptz default now()
);

-- 3. Tabla de Oportunidades (Matches)
-- Resultados del cruce inteligente (Gemini).
create table if not exists opportunities (
  id bigint primary key generated always as identity,
  client_name text,
  trend_title text,
  match_score int,
  reasoning jsonb, -- Lista de razones [str, str]
  generated_pitch text,
  created_at timestamptz default now()
);

-- 4. Tabla de Fuentes RSS (Gestión Avanzada)
-- Permite fuentes globales y específicas por cliente.
create table if not exists rss_sources (
  id bigint primary key generated always as identity,
  name text not null,
  url text not null unique,
  category text,
  client_id bigint references clients(id), -- NULL = Global, ID = Exclusiva del cliente
  is_active boolean default true,
  created_at timestamptz default now()
);

-- SEED DATA: Fuentes Globales Iniciales
insert into rss_sources (name, url, category) values 
  ('TechCrunch AI', 'https://techcrunch.com/category/artificial-intelligence/feed/', 'Tecnología'),
  ('MIT Technology Review', 'https://www.technologyreview.com/feed/', 'Innovación'),
  ('OpenAI Blog', 'https://openai.com/blog/rss.xml', 'AI Research'),
  ('VentureBeat AI', 'https://venturebeat.com/category/ai-strategy/feed/', 'Negocios')
on conflict (url) do nothing;
