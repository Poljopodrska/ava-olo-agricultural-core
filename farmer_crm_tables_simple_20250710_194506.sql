-- Farmer CRM Database Tables
-- Generated from Windows PostgreSQL
-- Date: 2025-07-10 19:45:06

CREATE TABLE public.advice_log (
    id integer NOT NULL,
    farmer_id integer NOT NULL,
    field_id integer,
    advice_text text NOT NULL,
    status character varying(20) DEFAULT 'pending'::character varying,
    "timestamp" timestamp without time zone NOT NULL,
    approved_by integer
);

CREATE TABLE public.consultation_triggers (
    id integer NOT NULL,
    trigger_type character varying(20),
    trigger_value character varying(100),
    description text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE public.conversation_state (
    phone_number character varying(20) NOT NULL,
    current_step integer DEFAULT 0,
    expected_yield double precision,
    soil_analysis boolean,
    fertilizer_stock boolean,
    npk_ratio character varying(20),
    last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE public.conversation_states (
    phone_number character varying(20) NOT NULL,
    state jsonb NOT NULL
);

CREATE TABLE public.cp_products (
    id integer NOT NULL,
    product_name character varying(100) NOT NULL,
    application_rate character varying(50),
    target_issue character varying(100),
    approved_crops character varying(200),
    crop_hr character varying(100),
    crop_lat character varying(100),
    pest_hr character varying(100),
    pest_lat character varying(100),
    dose character varying(50),
    pre_harvest_interval integer,
    remarks text,
    expiry date,
    source_file character varying(255),
    country character varying(50) DEFAULT 'Croatia'::character varying
);

CREATE TABLE public.crop_nutrient_needs (
    id integer NOT NULL,
    crop character varying(100) NOT NULL,
    expected_yield_t_ha numeric(10,2),
    p2o5_need_per_ton_kg_ton character varying(50),
    k2o_need_per_ton_kg_ton character varying(50),
    n_to_reach_expected_yield_kg_ha numeric(10,2),
    n_change_per_ton_yield_kg_ha_ton character varying(50),
    n_minimum_regarding_kg_ha character varying(50),
    n_maximum_regarding_kg_ha character varying(50),
    other_elements_per_ton text,
    notes text
);

CREATE TABLE public.crop_protection_croatia (
    id integer NOT NULL,
    product_name character varying(100) NOT NULL,
    crop_hr character varying(100) NOT NULL,
    crop_lat character varying(100),
    pest_hr character varying(100),
    pest_lat character varying(100),
    dose text,
    pre_harvest_interval character varying(50),
    remarks text,
    expiry date,
    source_file character varying(50)
);

CREATE TABLE public.crop_technology (
    id integer NOT NULL,
    crop_name character varying(50) NOT NULL,
    stage character varying(50) NOT NULL,
    action character varying(100) NOT NULL,
    timing character varying(100) NOT NULL,
    inputs text,
    notes text
);

CREATE TABLE public.farm_machinery (
    id integer NOT NULL,
    farm_id integer,
    category character varying(50),
    subcategory character varying(50),
    year_of_production integer,
    year_of_purchase integer,
    purchase_price double precision,
    producer character varying(50),
    model character varying(50),
    horsepower_tractor integer,
    has_navigation boolean,
    navigation_producer character varying(50),
    navigation_model character varying(50),
    navigation_reads_maps boolean,
    navigation_reads_maps_producer character varying(50),
    navigation_reads_maps_model character varying(50),
    horsepower_harvester integer,
    harvesting_width_cereals double precision,
    harvesting_width_maize double precision,
    harvesting_width_sunflower double precision,
    can_map_yield boolean,
    sowing_units_maize integer,
    can_add_fertilizer_maize boolean,
    can_add_microgranules_maize boolean,
    distance_between_units_cm double precision,
    distance_variable boolean,
    can_read_prescription_maps_maize boolean,
    distance_between_rows_cereals double precision,
    can_add_fertilizer_cereals boolean,
    can_add_microgranules_cereals boolean,
    width_sowing_cereals double precision,
    can_read_prescription_maps_cereals boolean,
    plough_bodies integer,
    plough_size integer,
    "podriva─Ź_width" double precision,
    "sjetvosprema─Ź_producer" character varying(50),
    "sjetvosprema─Ź_model" character varying(50),
    "sjetvosprema─Ź_width" double precision,
    rotobrana_width double precision,
    fertilizer_spreader_producer character varying(50),
    fertilizer_spreader_model character varying(50),
    can_read_prescription_maps_spreader boolean,
    can_adjust_quantity_from_cabin boolean,
    cultivation_width_maize double precision,
    can_add_fertilizer_cultivation boolean,
    sprayer_width double precision,
    has_section_control boolean,
    can_read_prescription_maps_sprayer boolean,
    notes text
);

CREATE TABLE public.farm_organic_fertilizers (
    id integer NOT NULL,
    farm_id integer,
    fertilizer_id integer,
    npk_composition character varying(20),
    analysis_date date,
    notes text
);

CREATE TABLE public.farmers (
    id integer NOT NULL,
    state_farm_number character varying(50),
    farm_name character varying(100),
    manager_name character varying(50),
    manager_last_name character varying(50),
    street_and_no character varying(100),
    village character varying(100),
    postal_code character varying(20),
    city character varying(100),
    country character varying(50),
    vat_no character varying(50),
    email character varying(100),
    phone character varying(20),
    wa_phone_number character varying(20),
    notes text
);

CREATE TABLE public.fertilizers (
    id integer NOT NULL,
    product_name character varying(100) NOT NULL,
    npk_composition character varying(20),
    notes text,
    common_name character varying(50),
    is_organic boolean DEFAULT false,
    is_calcification boolean DEFAULT false,
    ca_content double precision,
    country character varying(50) DEFAULT 'Croatia'::character varying,
    producer character varying(50),
    formulations character varying(20),
    granulation character varying(50)
);

CREATE TABLE public.fertilizing_plans (
    field_id integer NOT NULL,
    year integer NOT NULL,
    crop_name character varying(100) NOT NULL,
    p2o5_kg_ha double precision,
    p2o5_kg_field double precision,
    k2o_kg_ha double precision,
    k2o_kg_field double precision,
    n_kg_ha double precision,
    n_kg_field double precision,
    fertilizer_recommendation text,
    CONSTRAINT valid_year CHECK (((year >= 2025) AND (year <= 2029)))
);

CREATE TABLE public.field_crops (
    field_id integer NOT NULL,
    start_year_int integer NOT NULL,
    crop_name character varying(100) NOT NULL,
    variety character varying(100),
    expected_yield_t_ha double precision,
    start_date date,
    end_date date
);

CREATE TABLE public.field_soil_data (
    field_id integer NOT NULL,
    analysis_date date NOT NULL,
    ph double precision,
    p2o5_mg_100g double precision,
    k2o_mg_100g double precision,
    organic_matter_percent double precision,
    analysis_method character varying(50),
    analysis_institution character varying(100)
);

CREATE TABLE public.fields (
    id integer NOT NULL,
    farmer_id integer,
    field_name character varying(100) NOT NULL,
    area_ha double precision NOT NULL,
    latitude double precision,
    longitude double precision,
    blok_id character varying,
    raba character varying,
    nup_m2 double precision,
    povprecna_nmv double precision,
    povprecna_ekspozicija character varying,
    povprecni_naklon double precision,
    notes text,
    country character varying DEFAULT 'Croatia'::character varying,
    field_state_id character varying
);

CREATE TABLE public.growth_stage_reports (
    id integer NOT NULL,
    field_id integer NOT NULL,
    crop_name character varying(100) NOT NULL,
    variety character varying(100),
    growth_stage character varying(100) NOT NULL,
    date_reported date NOT NULL,
    farmer_id integer NOT NULL,
    reported_via character varying(50),
    notes text
);

CREATE TABLE public.incoming_messages (
    id integer NOT NULL,
    farmer_id integer NOT NULL,
    phone_number character varying(20) NOT NULL,
    message_text text NOT NULL,
    "timestamp" timestamp without time zone NOT NULL,
    role character varying(10) DEFAULT 'user'::character varying
);

CREATE TABLE public.inventory (
    id integer NOT NULL,
    farmer_id integer,
    material_id integer,
    quantity double precision,
    unit character varying,
    purchase_date date,
    purchase_price double precision,
    source_invoice_id integer,
    notes text
);

CREATE TABLE public.inventory_deductions (
    id integer NOT NULL,
    task_id integer NOT NULL,
    inventory_id integer NOT NULL,
    quantity_used double precision NOT NULL,
    created_at timestamp without time zone DEFAULT now()
);

CREATE TABLE public.invoices (
    id integer NOT NULL,
    farmer_id integer,
    upload_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    file_path character varying(255),
    extracted_data jsonb,
    status character varying(20) DEFAULT 'pending'::character varying,
    needs_verification boolean DEFAULT false,
    notes text
);

CREATE TABLE public.material_catalog (
    id integer NOT NULL,
    name character varying NOT NULL,
    brand character varying,
    group_name character varying,
    formulation character varying,
    unit character varying,
    notes text
);

CREATE TABLE public.orders (
    id integer NOT NULL,
    user_id integer,
    total_amount numeric(10,2),
    order_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE public.other_inputs (
    id integer NOT NULL,
    product_name character varying(100) NOT NULL,
    category character varying(50),
    description text,
    notes text,
    country character varying(50) DEFAULT 'Croatia'::character varying
);

CREATE TABLE public.pending_messages (
    id integer NOT NULL,
    farmer_id integer,
    phone_number character varying(20),
    message_text text,
    status character varying(20) DEFAULT 'pending'::character varying,
    requires_consultation boolean DEFAULT false,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE public.seeds (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    crop_type character varying(50),
    notes text,
    producer character varying(50),
    maturity_group character varying(50),
    purpose character varying(50),
    plant_density_from integer,
    plant_density_to integer,
    unit_for_sowing_rate character varying(20),
    country character varying(50) DEFAULT 'Croatia'::character varying
);

CREATE TABLE public.task_fields (
    task_id integer NOT NULL,
    field_id integer NOT NULL
);

CREATE TABLE public.task_material_dose (
    task_type text NOT NULL,
    material_id integer NOT NULL,
    crop_name text NOT NULL,
    year integer NOT NULL,
    farmer_id integer NOT NULL,
    rate_per_ha double precision NOT NULL,
    rate_unit text NOT NULL
);

CREATE TABLE public.task_materials (
    task_id integer NOT NULL,
    inventory_id integer NOT NULL,
    quantity double precision
);

CREATE TABLE public.task_types (
    id integer NOT NULL,
    name character varying NOT NULL,
    description text
);

CREATE TABLE public.tasks (
    id integer NOT NULL,
    task_type character varying(50) NOT NULL,
    description text,
    quantity double precision,
    date_performed date,
    status character varying(20) DEFAULT 'pending'::character varying,
    inventory_id integer,
    notes text,
    crop_name character varying(50),
    machinery_id integer,
    rate_per_ha double precision,
    rate_unit text
);

CREATE TABLE public.users (
    id integer NOT NULL,
    username character varying(50) NOT NULL,
    email character varying(100) NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE public.variety_trial_data (
    id integer NOT NULL,
    name character varying(50),
    crop_type character varying(50),
    producer character varying(50),
    maturity_group character varying(50),
    purpose character varying(50),
    plant_density_from integer,
    plant_density_to integer,
    unit_for_sowing_rate character varying(20),
    location character varying(100),
    sowing_date date,
    harvest_date date,
    plants_per_ha integer,
    moisture_at_harvest double precision,
    yield_kg_ha double precision,
    soil_type character varying(50),
    weather_conditions character varying(100),
    fertilization_used character varying(100),
    pest_resistance character varying(50),
    disease_incidence character varying(100),
    notes text
);

CREATE TABLE public.weather_data (
    id integer NOT NULL,
    field_id integer NOT NULL,
    fetch_date timestamp without time zone NOT NULL,
    latitude double precision NOT NULL,
    longitude double precision NOT NULL,
    current_temp_c double precision,
    current_soil_temp_10cm_c double precision,
    current_precip_mm double precision,
    current_humidity double precision,
    forecast jsonb
);