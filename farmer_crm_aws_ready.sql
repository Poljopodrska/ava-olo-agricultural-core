--
-- PostgreSQL database dump
--

-- Dumped from database version 16.9 (Ubuntu 16.9-0ubuntu0.24.04.1)
-- Dumped by pg_dump version 16.9 (Ubuntu 16.9-0ubuntu0.24.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: SCHEMA "public"; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON SCHEMA "public" IS 'standard public schema';


SET default_table_access_method = "heap";

--
-- Name: advice_log; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "public"."advice_log" (
    "id" integer NOT NULL,
    "farmer_id" integer NOT NULL,
    "field_id" integer,
    "advice_text" "text" NOT NULL,
    "status" character varying(20) DEFAULT 'pending'::character varying,
    "timestamp" timestamp without time zone NOT NULL,
    "approved_by" integer
);


--
-- Name: advice_log_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE "public"."advice_log_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: advice_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE "public"."advice_log_id_seq" OWNED BY "public"."advice_log"."id";


--
-- Name: consultation_triggers; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "public"."consultation_triggers" (
    "id" integer NOT NULL,
    "trigger_type" character varying(20),
    "trigger_value" character varying(100),
    "description" "text",
    "created_at" timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: consultation_triggers_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE "public"."consultation_triggers_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: consultation_triggers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE "public"."consultation_triggers_id_seq" OWNED BY "public"."consultation_triggers"."id";


--
-- Name: conversation_state; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "public"."conversation_state" (
    "phone_number" character varying(20) NOT NULL,
    "current_step" integer DEFAULT 0,
    "expected_yield" double precision,
    "soil_analysis" boolean,
    "fertilizer_stock" boolean,
    "npk_ratio" character varying(20),
    "last_updated" timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: conversation_states; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "public"."conversation_states" (
    "phone_number" character varying(20) NOT NULL,
    "state" "jsonb" NOT NULL
);


--
-- Name: cp_products; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "public"."cp_products" (
    "id" integer NOT NULL,
    "product_name" character varying(100) NOT NULL,
    "application_rate" character varying(50),
    "target_issue" character varying(100),
    "approved_crops" character varying(200),
    "crop_hr" character varying(100),
    "crop_lat" character varying(100),
    "pest_hr" character varying(100),
    "pest_lat" character varying(100),
    "dose" character varying(50),
    "pre_harvest_interval" integer,
    "remarks" "text",
    "expiry" "date",
    "source_file" character varying(255),
    "country" character varying(50) DEFAULT 'Croatia'::character varying
);


--
-- Name: cp_products_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE "public"."cp_products_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: cp_products_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE "public"."cp_products_id_seq" OWNED BY "public"."cp_products"."id";


--
-- Name: crop_nutrient_needs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "public"."crop_nutrient_needs" (
    "id" integer NOT NULL,
    "crop" character varying(100) NOT NULL,
    "expected_yield_t_ha" numeric(10,2),
    "p2o5_need_per_ton_kg_ton" character varying(50),
    "k2o_need_per_ton_kg_ton" character varying(50),
    "n_to_reach_expected_yield_kg_ha" numeric(10,2),
    "n_change_per_ton_yield_kg_ha_ton" character varying(50),
    "n_minimum_regarding_kg_ha" character varying(50),
    "n_maximum_regarding_kg_ha" character varying(50),
    "other_elements_per_ton" "text",
    "notes" "text"
);


--
-- Name: crop_nutrient_needs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE "public"."crop_nutrient_needs_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: crop_nutrient_needs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE "public"."crop_nutrient_needs_id_seq" OWNED BY "public"."crop_nutrient_needs"."id";


--
-- Name: crop_protection_croatia; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "public"."crop_protection_croatia" (
    "id" integer NOT NULL,
    "product_name" character varying(100) NOT NULL,
    "crop_hr" character varying(100) NOT NULL,
    "crop_lat" character varying(100),
    "pest_hr" character varying(100),
    "pest_lat" character varying(100),
    "dose" "text",
    "pre_harvest_interval" character varying(50),
    "remarks" "text",
    "expiry" "date",
    "source_file" character varying(50)
);


--
-- Name: crop_protection_croatia_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE "public"."crop_protection_croatia_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: crop_protection_croatia_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE "public"."crop_protection_croatia_id_seq" OWNED BY "public"."crop_protection_croatia"."id";


--
-- Name: crop_technology; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "public"."crop_technology" (
    "id" integer NOT NULL,
    "crop_name" character varying(50) NOT NULL,
    "stage" character varying(50) NOT NULL,
    "action" character varying(100) NOT NULL,
    "timing" character varying(100) NOT NULL,
    "inputs" "text",
    "notes" "text"
);


--
-- Name: crop_technology_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE "public"."crop_technology_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: crop_technology_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE "public"."crop_technology_id_seq" OWNED BY "public"."crop_technology"."id";


--
-- Name: farm_machinery; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "public"."farm_machinery" (
    "id" integer NOT NULL,
    "farm_id" integer,
    "category" character varying(50),
    "subcategory" character varying(50),
    "year_of_production" integer,
    "year_of_purchase" integer,
    "purchase_price" double precision,
    "producer" character varying(50),
    "model" character varying(50),
    "horsepower_tractor" integer,
    "has_navigation" boolean,
    "navigation_producer" character varying(50),
    "navigation_model" character varying(50),
    "navigation_reads_maps" boolean,
    "navigation_reads_maps_producer" character varying(50),
    "navigation_reads_maps_model" character varying(50),
    "horsepower_harvester" integer,
    "harvesting_width_cereals" double precision,
    "harvesting_width_maize" double precision,
    "harvesting_width_sunflower" double precision,
    "can_map_yield" boolean,
    "sowing_units_maize" integer,
    "can_add_fertilizer_maize" boolean,
    "can_add_microgranules_maize" boolean,
    "distance_between_units_cm" double precision,
    "distance_variable" boolean,
    "can_read_prescription_maps_maize" boolean,
    "distance_between_rows_cereals" double precision,
    "can_add_fertilizer_cereals" boolean,
    "can_add_microgranules_cereals" boolean,
    "width_sowing_cereals" double precision,
    "can_read_prescription_maps_cereals" boolean,
    "plough_bodies" integer,
    "plough_size" integer,
    "podriva─Ź_width" double precision,
    "sjetvosprema─Ź_producer" character varying(50),
    "sjetvosprema─Ź_model" character varying(50),
    "sjetvosprema─Ź_width" double precision,
    "rotobrana_width" double precision,
    "fertilizer_spreader_producer" character varying(50),
    "fertilizer_spreader_model" character varying(50),
    "can_read_prescription_maps_spreader" boolean,
    "can_adjust_quantity_from_cabin" boolean,
    "cultivation_width_maize" double precision,
    "can_add_fertilizer_cultivation" boolean,
    "sprayer_width" double precision,
    "has_section_control" boolean,
    "can_read_prescription_maps_sprayer" boolean,
    "notes" "text"
);


--
-- Name: farm_machinery_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE "public"."farm_machinery_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: farm_machinery_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE "public"."farm_machinery_id_seq" OWNED BY "public"."farm_machinery"."id";


--
-- Name: farm_organic_fertilizers; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "public"."farm_organic_fertilizers" (
    "id" integer NOT NULL,
    "farm_id" integer,
    "fertilizer_id" integer,
    "npk_composition" character varying(20),
    "analysis_date" "date",
    "notes" "text"
);


--
-- Name: farm_organic_fertilizers_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE "public"."farm_organic_fertilizers_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: farm_organic_fertilizers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE "public"."farm_organic_fertilizers_id_seq" OWNED BY "public"."farm_organic_fertilizers"."id";


--
-- Name: farmers; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "public"."farmers" (
    "id" integer NOT NULL,
    "state_farm_number" character varying(50),
    "farm_name" character varying(100),
    "manager_name" character varying(50),
    "manager_last_name" character varying(50),
    "street_and_no" character varying(100),
    "village" character varying(100),
    "postal_code" character varying(20),
    "city" character varying(100),
    "country" character varying(50),
    "vat_no" character varying(50),
    "email" character varying(100),
    "phone" character varying(20),
    "wa_phone_number" character varying(20),
    "notes" "text"
);


--
-- Name: farmers_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE "public"."farmers_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: farmers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE "public"."farmers_id_seq" OWNED BY "public"."farmers"."id";


--
-- Name: fertilizers; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "public"."fertilizers" (
    "id" integer NOT NULL,
    "product_name" character varying(100) NOT NULL,
    "npk_composition" character varying(20),
    "notes" "text",
    "common_name" character varying(50),
    "is_organic" boolean DEFAULT false,
    "is_calcification" boolean DEFAULT false,
    "ca_content" double precision,
    "country" character varying(50) DEFAULT 'Croatia'::character varying,
    "producer" character varying(50),
    "formulations" character varying(20),
    "granulation" character varying(50)
);


--
-- Name: fertilizers_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE "public"."fertilizers_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: fertilizers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE "public"."fertilizers_id_seq" OWNED BY "public"."fertilizers"."id";


--
-- Name: fertilizing_plans; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "public"."fertilizing_plans" (
    "field_id" integer NOT NULL,
    "year" integer NOT NULL,
    "crop_name" character varying(100) NOT NULL,
    "p2o5_kg_ha" double precision,
    "p2o5_kg_field" double precision,
    "k2o_kg_ha" double precision,
    "k2o_kg_field" double precision,
    "n_kg_ha" double precision,
    "n_kg_field" double precision,
    "fertilizer_recommendation" "text",
    CONSTRAINT "valid_year" CHECK ((("year" >= 2025) AND ("year" <= 2029)))
);


--
-- Name: field_crops; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "public"."field_crops" (
    "field_id" integer NOT NULL,
    "start_year_int" integer NOT NULL,
    "crop_name" character varying(100) NOT NULL,
    "variety" character varying(100),
    "expected_yield_t_ha" double precision,
    "start_date" "date",
    "end_date" "date"
);


--
-- Name: field_soil_data; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "public"."field_soil_data" (
    "field_id" integer NOT NULL,
    "analysis_date" "date" NOT NULL,
    "ph" double precision,
    "p2o5_mg_100g" double precision,
    "k2o_mg_100g" double precision,
    "organic_matter_percent" double precision,
    "analysis_method" character varying(50),
    "analysis_institution" character varying(100)
);


--
-- Name: fields; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "public"."fields" (
    "id" integer NOT NULL,
    "farmer_id" integer,
    "field_name" character varying(100) NOT NULL,
    "area_ha" double precision NOT NULL,
    "latitude" double precision,
    "longitude" double precision,
    "blok_id" character varying,
    "raba" character varying,
    "nup_m2" double precision,
    "povprecna_nmv" double precision,
    "povprecna_ekspozicija" character varying,
    "povprecni_naklon" double precision,
    "notes" "text",
    "country" character varying DEFAULT 'Croatia'::character varying,
    "field_state_id" character varying
);


--
-- Name: fields_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE "public"."fields_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: fields_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE "public"."fields_id_seq" OWNED BY "public"."fields"."id";


--
-- Name: growth_stage_reports; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "public"."growth_stage_reports" (
    "id" integer NOT NULL,
    "field_id" integer NOT NULL,
    "crop_name" character varying(100) NOT NULL,
    "variety" character varying(100),
    "growth_stage" character varying(100) NOT NULL,
    "date_reported" "date" NOT NULL,
    "farmer_id" integer NOT NULL,
    "reported_via" character varying(50),
    "notes" "text"
);


--
-- Name: growth_stage_reports_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE "public"."growth_stage_reports_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: growth_stage_reports_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE "public"."growth_stage_reports_id_seq" OWNED BY "public"."growth_stage_reports"."id";


--
-- Name: incoming_messages; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "public"."incoming_messages" (
    "id" integer NOT NULL,
    "farmer_id" integer NOT NULL,
    "phone_number" character varying(20) NOT NULL,
    "message_text" "text" NOT NULL,
    "timestamp" timestamp without time zone NOT NULL,
    "role" character varying(10) DEFAULT 'user'::character varying
);


--
-- Name: incoming_messages_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE "public"."incoming_messages_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: incoming_messages_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE "public"."incoming_messages_id_seq" OWNED BY "public"."incoming_messages"."id";


--
-- Name: inventory; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "public"."inventory" (
    "id" integer NOT NULL,
    "farmer_id" integer,
    "material_id" integer,
    "quantity" double precision,
    "unit" character varying,
    "purchase_date" "date",
    "purchase_price" double precision,
    "source_invoice_id" integer,
    "notes" "text"
);


--
-- Name: inventory_deductions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "public"."inventory_deductions" (
    "id" integer NOT NULL,
    "task_id" integer NOT NULL,
    "inventory_id" integer NOT NULL,
    "quantity_used" double precision NOT NULL,
    "created_at" timestamp without time zone DEFAULT "now"()
);


--
-- Name: inventory_deductions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE "public"."inventory_deductions_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: inventory_deductions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE "public"."inventory_deductions_id_seq" OWNED BY "public"."inventory_deductions"."id";


--
-- Name: inventory_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE "public"."inventory_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: inventory_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE "public"."inventory_id_seq" OWNED BY "public"."inventory"."id";


--
-- Name: invoices; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "public"."invoices" (
    "id" integer NOT NULL,
    "farmer_id" integer,
    "upload_date" timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    "file_path" character varying(255),
    "extracted_data" "jsonb",
    "status" character varying(20) DEFAULT 'pending'::character varying,
    "needs_verification" boolean DEFAULT false,
    "notes" "text"
);


--
-- Name: invoices_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE "public"."invoices_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: invoices_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE "public"."invoices_id_seq" OWNED BY "public"."invoices"."id";


--
-- Name: material_catalog; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "public"."material_catalog" (
    "id" integer NOT NULL,
    "name" character varying NOT NULL,
    "brand" character varying,
    "group_name" character varying,
    "formulation" character varying,
    "unit" character varying,
    "notes" "text"
);


--
-- Name: material_catalog_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE "public"."material_catalog_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: material_catalog_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE "public"."material_catalog_id_seq" OWNED BY "public"."material_catalog"."id";


--
-- Name: orders; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "public"."orders" (
    "id" integer NOT NULL,
    "user_id" integer,
    "total_amount" numeric(10,2),
    "order_date" timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: orders_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE "public"."orders_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: orders_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE "public"."orders_id_seq" OWNED BY "public"."orders"."id";


--
-- Name: other_inputs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "public"."other_inputs" (
    "id" integer NOT NULL,
    "product_name" character varying(100) NOT NULL,
    "category" character varying(50),
    "description" "text",
    "notes" "text",
    "country" character varying(50) DEFAULT 'Croatia'::character varying
);


--
-- Name: other_inputs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE "public"."other_inputs_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: other_inputs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE "public"."other_inputs_id_seq" OWNED BY "public"."other_inputs"."id";


--
-- Name: pending_messages; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "public"."pending_messages" (
    "id" integer NOT NULL,
    "farmer_id" integer,
    "phone_number" character varying(20),
    "message_text" "text",
    "status" character varying(20) DEFAULT 'pending'::character varying,
    "requires_consultation" boolean DEFAULT false,
    "created_at" timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: pending_messages_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE "public"."pending_messages_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: pending_messages_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE "public"."pending_messages_id_seq" OWNED BY "public"."pending_messages"."id";


--
-- Name: seeds; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "public"."seeds" (
    "id" integer NOT NULL,
    "name" character varying(100) NOT NULL,
    "crop_type" character varying(50),
    "notes" "text",
    "producer" character varying(50),
    "maturity_group" character varying(50),
    "purpose" character varying(50),
    "plant_density_from" integer,
    "plant_density_to" integer,
    "unit_for_sowing_rate" character varying(20),
    "country" character varying(50) DEFAULT 'Croatia'::character varying
);


--
-- Name: seeds_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE "public"."seeds_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: seeds_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE "public"."seeds_id_seq" OWNED BY "public"."seeds"."id";


--
-- Name: task_fields; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "public"."task_fields" (
    "task_id" integer NOT NULL,
    "field_id" integer NOT NULL
);


--
-- Name: task_material_dose; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "public"."task_material_dose" (
    "task_type" "text" NOT NULL,
    "material_id" integer NOT NULL,
    "crop_name" "text" NOT NULL,
    "year" integer NOT NULL,
    "farmer_id" integer NOT NULL,
    "rate_per_ha" double precision NOT NULL,
    "rate_unit" "text" NOT NULL
);


--
-- Name: task_materials; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "public"."task_materials" (
    "task_id" integer NOT NULL,
    "inventory_id" integer NOT NULL,
    "quantity" double precision
);


--
-- Name: task_types; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "public"."task_types" (
    "id" integer NOT NULL,
    "name" character varying NOT NULL,
    "description" "text"
);


--
-- Name: task_types_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE "public"."task_types_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: task_types_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE "public"."task_types_id_seq" OWNED BY "public"."task_types"."id";


--
-- Name: tasks; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "public"."tasks" (
    "id" integer NOT NULL,
    "task_type" character varying(50) NOT NULL,
    "description" "text",
    "quantity" double precision,
    "date_performed" "date",
    "status" character varying(20) DEFAULT 'pending'::character varying,
    "inventory_id" integer,
    "notes" "text",
    "crop_name" character varying(50),
    "machinery_id" integer,
    "rate_per_ha" double precision,
    "rate_unit" "text"
);


--
-- Name: tasks_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE "public"."tasks_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: tasks_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE "public"."tasks_id_seq" OWNED BY "public"."tasks"."id";


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "public"."users" (
    "id" integer NOT NULL,
    "username" character varying(50) NOT NULL,
    "email" character varying(100) NOT NULL,
    "created_at" timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE "public"."users_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE "public"."users_id_seq" OWNED BY "public"."users"."id";


--
-- Name: variety_trial_data; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "public"."variety_trial_data" (
    "id" integer NOT NULL,
    "name" character varying(50),
    "crop_type" character varying(50),
    "producer" character varying(50),
    "maturity_group" character varying(50),
    "purpose" character varying(50),
    "plant_density_from" integer,
    "plant_density_to" integer,
    "unit_for_sowing_rate" character varying(20),
    "location" character varying(100),
    "sowing_date" "date",
    "harvest_date" "date",
    "plants_per_ha" integer,
    "moisture_at_harvest" double precision,
    "yield_kg_ha" double precision,
    "soil_type" character varying(50),
    "weather_conditions" character varying(100),
    "fertilization_used" character varying(100),
    "pest_resistance" character varying(50),
    "disease_incidence" character varying(100),
    "notes" "text"
);


--
-- Name: variety_trial_data_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE "public"."variety_trial_data_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: variety_trial_data_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE "public"."variety_trial_data_id_seq" OWNED BY "public"."variety_trial_data"."id";


--
-- Name: weather_data; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "public"."weather_data" (
    "id" integer NOT NULL,
    "field_id" integer NOT NULL,
    "fetch_date" timestamp without time zone NOT NULL,
    "latitude" double precision NOT NULL,
    "longitude" double precision NOT NULL,
    "current_temp_c" double precision,
    "current_soil_temp_10cm_c" double precision,
    "current_precip_mm" double precision,
    "current_humidity" double precision,
    "forecast" "jsonb"
);


--
-- Name: weather_data_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE "public"."weather_data_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: weather_data_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE "public"."weather_data_id_seq" OWNED BY "public"."weather_data"."id";


--
-- Name: advice_log id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."advice_log" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."advice_log_id_seq"'::"regclass");


--
-- Name: consultation_triggers id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."consultation_triggers" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."consultation_triggers_id_seq"'::"regclass");


--
-- Name: cp_products id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."cp_products" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."cp_products_id_seq"'::"regclass");


--
-- Name: crop_nutrient_needs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."crop_nutrient_needs" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."crop_nutrient_needs_id_seq"'::"regclass");


--
-- Name: crop_protection_croatia id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."crop_protection_croatia" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."crop_protection_croatia_id_seq"'::"regclass");


--
-- Name: crop_technology id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."crop_technology" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."crop_technology_id_seq"'::"regclass");


--
-- Name: farm_machinery id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."farm_machinery" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."farm_machinery_id_seq"'::"regclass");


--
-- Name: farm_organic_fertilizers id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."farm_organic_fertilizers" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."farm_organic_fertilizers_id_seq"'::"regclass");


--
-- Name: farmers id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."farmers" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."farmers_id_seq"'::"regclass");


--
-- Name: fertilizers id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."fertilizers" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."fertilizers_id_seq"'::"regclass");


--
-- Name: fields id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."fields" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."fields_id_seq"'::"regclass");


--
-- Name: growth_stage_reports id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."growth_stage_reports" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."growth_stage_reports_id_seq"'::"regclass");


--
-- Name: incoming_messages id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."incoming_messages" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."incoming_messages_id_seq"'::"regclass");


--
-- Name: inventory id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."inventory" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."inventory_id_seq"'::"regclass");


--
-- Name: inventory_deductions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."inventory_deductions" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."inventory_deductions_id_seq"'::"regclass");


--
-- Name: invoices id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."invoices" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."invoices_id_seq"'::"regclass");


--
-- Name: material_catalog id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."material_catalog" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."material_catalog_id_seq"'::"regclass");


--
-- Name: orders id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."orders" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."orders_id_seq"'::"regclass");


--
-- Name: other_inputs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."other_inputs" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."other_inputs_id_seq"'::"regclass");


--
-- Name: pending_messages id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."pending_messages" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."pending_messages_id_seq"'::"regclass");


--
-- Name: seeds id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."seeds" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."seeds_id_seq"'::"regclass");


--
-- Name: task_types id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."task_types" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."task_types_id_seq"'::"regclass");


--
-- Name: tasks id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."tasks" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."tasks_id_seq"'::"regclass");


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."users" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."users_id_seq"'::"regclass");


--
-- Name: variety_trial_data id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."variety_trial_data" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."variety_trial_data_id_seq"'::"regclass");


--
-- Name: weather_data id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."weather_data" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."weather_data_id_seq"'::"regclass");


--
-- Name: advice_log advice_log_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."advice_log"
    ADD CONSTRAINT "advice_log_pkey" PRIMARY KEY ("id");


--
-- Name: consultation_triggers consultation_triggers_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."consultation_triggers"
    ADD CONSTRAINT "consultation_triggers_pkey" PRIMARY KEY ("id");


--
-- Name: conversation_state conversation_state_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."conversation_state"
    ADD CONSTRAINT "conversation_state_pkey" PRIMARY KEY ("phone_number");


--
-- Name: conversation_states conversation_states_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."conversation_states"
    ADD CONSTRAINT "conversation_states_pkey" PRIMARY KEY ("phone_number");


--
-- Name: cp_products cp_products_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."cp_products"
    ADD CONSTRAINT "cp_products_pkey" PRIMARY KEY ("id");


--
-- Name: crop_nutrient_needs crop_nutrient_needs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."crop_nutrient_needs"
    ADD CONSTRAINT "crop_nutrient_needs_pkey" PRIMARY KEY ("id");


--
-- Name: crop_protection_croatia crop_protection_croatia_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."crop_protection_croatia"
    ADD CONSTRAINT "crop_protection_croatia_pkey" PRIMARY KEY ("id");


--
-- Name: crop_technology crop_technology_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."crop_technology"
    ADD CONSTRAINT "crop_technology_pkey" PRIMARY KEY ("id");


--
-- Name: farm_machinery farm_machinery_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."farm_machinery"
    ADD CONSTRAINT "farm_machinery_pkey" PRIMARY KEY ("id");


--
-- Name: farm_organic_fertilizers farm_organic_fertilizers_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."farm_organic_fertilizers"
    ADD CONSTRAINT "farm_organic_fertilizers_pkey" PRIMARY KEY ("id");


--
-- Name: farmers farmers_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."farmers"
    ADD CONSTRAINT "farmers_pkey" PRIMARY KEY ("id");


--
-- Name: farmers farmers_state_farm_number_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."farmers"
    ADD CONSTRAINT "farmers_state_farm_number_key" UNIQUE ("state_farm_number");


--
-- Name: fertilizers fertilizers_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."fertilizers"
    ADD CONSTRAINT "fertilizers_pkey" PRIMARY KEY ("id");


--
-- Name: fields fields_field_state_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."fields"
    ADD CONSTRAINT "fields_field_state_id_key" UNIQUE ("field_state_id");


--
-- Name: fields fields_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."fields"
    ADD CONSTRAINT "fields_pkey" PRIMARY KEY ("id");


--
-- Name: growth_stage_reports growth_stage_reports_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."growth_stage_reports"
    ADD CONSTRAINT "growth_stage_reports_pkey" PRIMARY KEY ("id");


--
-- Name: incoming_messages incoming_messages_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."incoming_messages"
    ADD CONSTRAINT "incoming_messages_pkey" PRIMARY KEY ("id");


--
-- Name: inventory_deductions inventory_deductions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."inventory_deductions"
    ADD CONSTRAINT "inventory_deductions_pkey" PRIMARY KEY ("id");


--
-- Name: inventory inventory_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."inventory"
    ADD CONSTRAINT "inventory_pkey" PRIMARY KEY ("id");


--
-- Name: invoices invoices_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."invoices"
    ADD CONSTRAINT "invoices_pkey" PRIMARY KEY ("id");


--
-- Name: material_catalog material_catalog_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."material_catalog"
    ADD CONSTRAINT "material_catalog_name_key" UNIQUE ("name");


--
-- Name: material_catalog material_catalog_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."material_catalog"
    ADD CONSTRAINT "material_catalog_pkey" PRIMARY KEY ("id");


--
-- Name: orders orders_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."orders"
    ADD CONSTRAINT "orders_pkey" PRIMARY KEY ("id");


--
-- Name: other_inputs other_inputs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."other_inputs"
    ADD CONSTRAINT "other_inputs_pkey" PRIMARY KEY ("id");


--
-- Name: pending_messages pending_messages_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."pending_messages"
    ADD CONSTRAINT "pending_messages_pkey" PRIMARY KEY ("id");


--
-- Name: seeds seeds_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."seeds"
    ADD CONSTRAINT "seeds_pkey" PRIMARY KEY ("id");


--
-- Name: task_material_dose task_material_dose_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."task_material_dose"
    ADD CONSTRAINT "task_material_dose_pkey" PRIMARY KEY ("task_type", "material_id", "crop_name", "year", "farmer_id");


--
-- Name: task_materials task_materials_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."task_materials"
    ADD CONSTRAINT "task_materials_pkey" PRIMARY KEY ("task_id", "inventory_id");


--
-- Name: task_types task_types_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."task_types"
    ADD CONSTRAINT "task_types_name_key" UNIQUE ("name");


--
-- Name: task_types task_types_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."task_types"
    ADD CONSTRAINT "task_types_pkey" PRIMARY KEY ("id");


--
-- Name: tasks tasks_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."tasks"
    ADD CONSTRAINT "tasks_pkey" PRIMARY KEY ("id");


--
-- Name: cp_products unique_cp_per_country; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."cp_products"
    ADD CONSTRAINT "unique_cp_per_country" UNIQUE ("product_name", "crop_hr", "pest_hr", "country");


--
-- Name: farmers unique_state_farm_number; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."farmers"
    ADD CONSTRAINT "unique_state_farm_number" UNIQUE ("state_farm_number");


--
-- Name: farmers unique_state_farm_number_per_country; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."farmers"
    ADD CONSTRAINT "unique_state_farm_number_per_country" UNIQUE ("state_farm_number", "country");


--
-- Name: farmers unique_vat_no; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."farmers"
    ADD CONSTRAINT "unique_vat_no" UNIQUE ("vat_no");


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."users"
    ADD CONSTRAINT "users_pkey" PRIMARY KEY ("id");


--
-- Name: users users_username_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."users"
    ADD CONSTRAINT "users_username_key" UNIQUE ("username");


--
-- Name: variety_trial_data variety_trial_data_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."variety_trial_data"
    ADD CONSTRAINT "variety_trial_data_pkey" PRIMARY KEY ("id");


--
-- Name: weather_data weather_data_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."weather_data"
    ADD CONSTRAINT "weather_data_pkey" PRIMARY KEY ("id");


--
-- Name: idx_weather_data_field_id_fetch_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "idx_weather_data_field_id_fetch_date" ON "public"."weather_data" USING "btree" ("field_id", "fetch_date");


--
-- Name: advice_log advice_log_farmer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."advice_log"
    ADD CONSTRAINT "advice_log_farmer_id_fkey" FOREIGN KEY ("farmer_id") REFERENCES "public"."farmers"("id");


--
-- Name: advice_log advice_log_field_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."advice_log"
    ADD CONSTRAINT "advice_log_field_id_fkey" FOREIGN KEY ("field_id") REFERENCES "public"."fields"("id");


--
-- Name: farm_machinery farm_machinery_farm_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."farm_machinery"
    ADD CONSTRAINT "farm_machinery_farm_id_fkey" FOREIGN KEY ("farm_id") REFERENCES "public"."farmers"("id");


--
-- Name: farm_organic_fertilizers farm_organic_fertilizers_farm_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."farm_organic_fertilizers"
    ADD CONSTRAINT "farm_organic_fertilizers_farm_id_fkey" FOREIGN KEY ("farm_id") REFERENCES "public"."farmers"("id");


--
-- Name: farm_organic_fertilizers farm_organic_fertilizers_fertilizer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."farm_organic_fertilizers"
    ADD CONSTRAINT "farm_organic_fertilizers_fertilizer_id_fkey" FOREIGN KEY ("fertilizer_id") REFERENCES "public"."fertilizers"("id");


--
-- Name: fields fk_farmer; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."fields"
    ADD CONSTRAINT "fk_farmer" FOREIGN KEY ("farmer_id") REFERENCES "public"."farmers"("id");


--
-- Name: growth_stage_reports fk_farmer; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."growth_stage_reports"
    ADD CONSTRAINT "fk_farmer" FOREIGN KEY ("farmer_id") REFERENCES "public"."farmers"("id");


--
-- Name: fertilizing_plans fk_field; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."fertilizing_plans"
    ADD CONSTRAINT "fk_field" FOREIGN KEY ("field_id") REFERENCES "public"."fields"("id");


--
-- Name: field_crops fk_field; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."field_crops"
    ADD CONSTRAINT "fk_field" FOREIGN KEY ("field_id") REFERENCES "public"."fields"("id");


--
-- Name: field_soil_data fk_field; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."field_soil_data"
    ADD CONSTRAINT "fk_field" FOREIGN KEY ("field_id") REFERENCES "public"."fields"("id");


--
-- Name: task_fields fk_field; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."task_fields"
    ADD CONSTRAINT "fk_field" FOREIGN KEY ("field_id") REFERENCES "public"."fields"("id");


--
-- Name: weather_data fk_field; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."weather_data"
    ADD CONSTRAINT "fk_field" FOREIGN KEY ("field_id") REFERENCES "public"."fields"("id");


--
-- Name: growth_stage_reports fk_field; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."growth_stage_reports"
    ADD CONSTRAINT "fk_field" FOREIGN KEY ("field_id") REFERENCES "public"."fields"("id");


--
-- Name: tasks fk_inventory_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."tasks"
    ADD CONSTRAINT "fk_inventory_id" FOREIGN KEY ("inventory_id") REFERENCES "public"."inventory"("id");


--
-- Name: incoming_messages incoming_messages_farmer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."incoming_messages"
    ADD CONSTRAINT "incoming_messages_farmer_id_fkey" FOREIGN KEY ("farmer_id") REFERENCES "public"."farmers"("id");


--
-- Name: inventory_deductions inventory_deductions_inventory_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."inventory_deductions"
    ADD CONSTRAINT "inventory_deductions_inventory_id_fkey" FOREIGN KEY ("inventory_id") REFERENCES "public"."inventory"("id") ON DELETE CASCADE;


--
-- Name: inventory_deductions inventory_deductions_task_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."inventory_deductions"
    ADD CONSTRAINT "inventory_deductions_task_id_fkey" FOREIGN KEY ("task_id") REFERENCES "public"."tasks"("id") ON DELETE CASCADE;


--
-- Name: inventory inventory_farmer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."inventory"
    ADD CONSTRAINT "inventory_farmer_id_fkey" FOREIGN KEY ("farmer_id") REFERENCES "public"."farmers"("id");


--
-- Name: inventory inventory_material_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."inventory"
    ADD CONSTRAINT "inventory_material_id_fkey" FOREIGN KEY ("material_id") REFERENCES "public"."material_catalog"("id");


--
-- Name: inventory inventory_source_invoice_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."inventory"
    ADD CONSTRAINT "inventory_source_invoice_id_fkey" FOREIGN KEY ("source_invoice_id") REFERENCES "public"."invoices"("id");


--
-- Name: invoices invoices_farmer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."invoices"
    ADD CONSTRAINT "invoices_farmer_id_fkey" FOREIGN KEY ("farmer_id") REFERENCES "public"."farmers"("id");


--
-- Name: orders orders_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."orders"
    ADD CONSTRAINT "orders_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


--
-- Name: pending_messages pending_messages_farmer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."pending_messages"
    ADD CONSTRAINT "pending_messages_farmer_id_fkey" FOREIGN KEY ("farmer_id") REFERENCES "public"."farmers"("id");


--
-- Name: task_material_dose task_material_dose_material_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."task_material_dose"
    ADD CONSTRAINT "task_material_dose_material_id_fkey" FOREIGN KEY ("material_id") REFERENCES "public"."material_catalog"("id");


--
-- Name: task_materials task_materials_inventory_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."task_materials"
    ADD CONSTRAINT "task_materials_inventory_id_fkey" FOREIGN KEY ("inventory_id") REFERENCES "public"."inventory"("id") ON DELETE SET NULL;


--
-- Name: task_materials task_materials_task_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."task_materials"
    ADD CONSTRAINT "task_materials_task_id_fkey" FOREIGN KEY ("task_id") REFERENCES "public"."tasks"("id") ON DELETE CASCADE;


--
-- Name: tasks tasks_machinery_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."tasks"
    ADD CONSTRAINT "tasks_machinery_id_fkey" FOREIGN KEY ("machinery_id") REFERENCES "public"."farm_machinery"("id");


--
-- PostgreSQL database dump complete
--

