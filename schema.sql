CREATE TABLE IF NOT EXISTS cities (
  city_id      smallserial PRIMARY KEY,
  name         text UNIQUE,
  state        text,
  pincode_from int,
  pincode_to   int
);

CREATE TABLE IF NOT EXISTS people (
  phone_pk        bigint,
  city_id         smallint,
  first_name      text,
  middle_name     text,
  last_name       text,
  full_name       text,
  name_confidence real,
  updated_at      timestamptz DEFAULT now(),
  PRIMARY KEY (phone_pk, city_id)
);

CREATE TABLE IF NOT EXISTS source_files (
  file_id     serial PRIMARY KEY,
  file_name   text,
  uploaded_at timestamptz DEFAULT now(),
  status      text CHECK (status IN ('processing','active','expired','failed'))
);

CREATE TABLE IF NOT EXISTS people_sources (
  phone_pk  bigint,
  city_id   smallint,
  file_id   int REFERENCES source_files,
  PRIMARY KEY (phone_pk, city_id, file_id)
);
