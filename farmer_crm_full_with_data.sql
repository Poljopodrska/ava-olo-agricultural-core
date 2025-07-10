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
-- Data for Name: advice_log; Type: TABLE DATA; Schema: public; Owner: -
--

COPY "public"."advice_log" ("id", "farmer_id", "field_id", "advice_text", "status", "timestamp", "approved_by") FROM stdin;
\.


--
-- Data for Name: consultation_triggers; Type: TABLE DATA; Schema: public; Owner: -
--

COPY "public"."consultation_triggers" ("id", "trigger_type", "trigger_value", "description", "created_at") FROM stdin;
\.


--
-- Data for Name: conversation_state; Type: TABLE DATA; Schema: public; Owner: -
--

COPY "public"."conversation_state" ("phone_number", "current_step", "expected_yield", "soil_analysis", "fertilizer_stock", "npk_ratio", "last_updated") FROM stdin;
+38641348050	5	5	\N	f	\N	2025-05-20 15:12:50.113839
+4915156006708	1	\N	\N	\N	\N	2025-05-21 00:08:43.284068
\.


--
-- Data for Name: conversation_states; Type: TABLE DATA; Schema: public; Owner: -
--

COPY "public"."conversation_states" ("phone_number", "state") FROM stdin;
38641348050	{"data": {"crop_name": "Travnik", "straw_removal": null, "expected_yield": null, "fertilizer_type": null, "fertilizer_stock": null, "has_soil_analysis": false}, "step": "expected_yield", "pending_input": null}
\.


--
-- Data for Name: cp_products; Type: TABLE DATA; Schema: public; Owner: -
--

COPY "public"."cp_products" ("id", "product_name", "application_rate", "target_issue", "approved_crops", "crop_hr", "crop_lat", "pest_hr", "pest_lat", "dose", "pre_harvest_interval", "remarks", "expiry", "source_file", "country") FROM stdin;
1	Mikal	3 kg/ha	Fusarium	Wheat	\N	\N	\N	\N	\N	\N	\N	\N	\N	Croatia
\.


--
-- Data for Name: crop_nutrient_needs; Type: TABLE DATA; Schema: public; Owner: -
--

COPY "public"."crop_nutrient_needs" ("id", "crop", "expected_yield_t_ha", "p2o5_need_per_ton_kg_ton", "k2o_need_per_ton_kg_ton", "n_to_reach_expected_yield_kg_ha", "n_change_per_ton_yield_kg_ha_ton", "n_minimum_regarding_kg_ha", "n_maximum_regarding_kg_ha", "other_elements_per_ton", "notes") FROM stdin;
1	Sugarbeet	60.00	1.11	3.33	170.00	3.2	100	200	\N	\N
2	Corn (grain)	10.00	7	4	170.00	10	160	210	\N	\N
3	Wheat (grain, straw left)	7.00	8	5	170.00	10	160	190	\N	\N
4	Wheat (grain + hay, straw removed)	7.00	11	20	170.00	10	160	190	\N	\N
5	Grapes	10.00	0.8	2.8	30.00	3	30	60	\N	\N
6	Grapes (wood removed after pruning)	10.00	1.5	5.3	50.00	3	50	80	\N	\N
7	Oilseed rape	3.50	18	10	140.00	40	120	200	\N	\N
8	Grass	10.00	1.6	6.5	100.00	10	80	150	\N	Merged with Carpet Grass Production
9	Pumpkin	1.00	70 (total kg/ha)	260 (total kg/ha)	60.00	\N	\N	\N	\N	\N
10	Regular Barley (grain, straw left)	6.00	8	6	100.00	10	100	130	\N	\N
11	Regular Barley (grain + hay, straw removed)	6.00	11	23	100.00	10	100	130	\N	\N
12	Barley for Brewing Industry (grain, straw left)	6.00	8	6	80.00	8	80	110	\N	\N
13	Barley for Brewing Industry (grain + hay, straw removed)	6.00	11	23	80.00	8	80	110	\N	\N
14	Buckwheat	1.50	1.3	4	60.00	10	50	80	\N	\N
15	Clover	10.00	1.3	6	20.00	0	20	20	Mg: 2 kg/ton, Ca: 20 kg/ton	\N
16	Cover Crop	3.00	0	0	0.00	0	0	0	\N	\N
17	Corn (silage)	40.00	1.6	4.5	160.00	2.5	160	210	\N	\N
18	Rye (grain, straw left)	7.00	8	6	170.00	10	160	190	\N	\N
19	Rye (grain + hay, straw removed)	5.00	11	26	80.00	8	80	110	\N	\N
20	Triticale (grain, straw left)	7.00	8	6	170.00	10	160	190	\N	\N
21	Triticale (grain + hay, straw removed)	5.00	11	23	80.00	8	80	110	\N	\N
22	Oats (grain, straw left)	7.00	8	6	170.00	10	160	190	\N	\N
23	Oats (grain + hay, straw removed)	4.00	11	25	60.00	8	60	80	\N	\N
24	Soya bean	3.00	14	20	50.00	\N	\N	\N	\N	\N
25	Asparagus	5.00	10	30	70.00	\N	\N	\N	Mg: 12 kg/ton, Ca: 8 kg/ton	\N
26	Broccoli	20.00	4	11	200.00	\N	\N	\N	Mg: 1.5 kg/ton, Ca: 3.5 kg/ton	\N
27	Brussels Sprouts	12.00	4.17	15.83	270.00	\N	\N	\N	Mg: 5.42 kg/ton, Ca: 2.08 kg/ton	\N
28	Zucchini (bush type)	40.00	1.38	5.25	150.00	\N	\N	\N	Mg: 0.63 kg/ton, Ca: 2.13 kg/ton	\N
29	Zucchini (vining type)	100.00	1.15	4.2	320.00	\N	\N	\N	Mg: 0.55 kg/ton, Ca: 2.1 kg/ton	\N
30	Chicory	30.00	1.33	3.67	160.00	\N	\N	\N	Mg: 0.33 kg/ton, Ca: 1 kg/ton	\N
31	Cauliflower	30.00	2.5	10	220.00	\N	\N	\N	Mg: 1.17 kg/ton, Ca: 2.17 kg/ton	\N
32	Onion	50.00	1.5	3.6	120.00	\N	\N	\N	Mg: 0.5 kg/ton, Ca: 0.7 kg/ton	\N
33	Garlic	4.50	20	33.33	75.00	\N	\N	\N	Mg: 3.33 kg/ton, Ca: 5.56 kg/ton	\N
34	Black Salsify	20.00	2.25	7.5	130.00	\N	\N	\N	Mg: 0.5 kg/ton, Ca: 3.2 kg/ton	\N
35	Chives	50.00	1.4	5	200.00	\N	\N	\N	Mg: 0.3 kg/ton, Ca: 1.08 kg/ton	\N
36	Endive	40.00	1	3.75	120.00	\N	\N	\N	Mg: 0.63 kg/ton, Ca: 0.5 kg/ton	\N
37	Bean (Pole Bean)	12.50	3.2	12	105.00	\N	\N	\N	Mg: 1.6 kg/ton, Ca: 16 kg/ton	Applies to both fresh beans (yield 12.5 t/ha) and dry grain (yield 2.5 t/ha)
38	Savoy Cabbage	40.00	2	7.5	300.00	\N	\N	\N	Mg: 3.13 kg/ton, Ca: 0.63 kg/ton	\N
39	Pea	7.50	5.33	20	70.00	\N	\N	\N	Mg: 2.67 kg/ton, Ca: 14 kg/ton	\N
40	Horseradish	10.00	5.5	21	160.00	\N	\N	\N	Mg: 3.5 kg/ton, Ca: 15 kg/ton	\N
41	Anise	20.00	1.75	6.5	90.00	\N	\N	\N	Mg: 0.9 kg/ton, Ca: 2.75 kg/ton	\N
42	Chinese Cabbage	50.00	1.2	4.7	200.00	\N	\N	\N	Mg: 0.8 kg/ton, Ca: 2.3 kg/ton	\N
43	Kohlrabi	30.00	1.5	6	150.00	\N	\N	\N	Mg: 0.67 kg/ton, Ca: 2.83 kg/ton	\N
44	Fennel	20.00	1.25	6.5	150.00	\N	\N	\N	Mg: 0.75 kg/ton, Ca: 2.25 kg/ton	\N
45	Carrot (storage)	70.00	1.29	5.71	175.00	\N	\N	\N	Mg: 1.07 kg/ton, Ca: 1.57 kg/ton	\N
46	Carrot (bunches)	50.00	1.68	6.86	110.00	\N	\N	\N	Mg: 0.78 kg/ton, Ca: 1.96 kg/ton	\N
47	Pickling Cucumbers	40.00	1.63	5.5	180.00	\N	\N	\N	Mg: 1 kg/ton, Ca: 5.5 kg/ton	\N
48	LambÔÇÖs Lettuce (Corn Salad)	10.00	1.5	5	60.00	\N	\N	\N	Mg: 0.5 kg/ton, Ca: 1 kg/ton	\N
49	Oil Pumpkin (seeds)	0.60	133.33	366.67	80.00	\N	\N	\N	Mg: 66.67 kg/ton, Ca: 300 kg/ton	\N
50	Pepper	40.00	1.13	4.5	180.00	\N	\N	\N	Mg: 0.75 kg/ton, Ca: 0.55 kg/ton	\N
51	Tomato	75.00	0.8	4	225.00	\N	\N	\N	Mg: 0.29 kg/ton, Ca: 0.51 kg/ton	\N
52	Parsnip	40.00	2	7.5	130.00	\N	\N	\N	Mg: 0.55 kg/ton, Ca: 2.15 kg/ton	\N
53	Parsley (root)	25.00	1.8	6.6	130.00	\N	\N	\N	Mg: 0.52 kg/ton, Ca: 2.88 kg/ton	\N
54	Parsley (cutting)	30.00	1.5	6	130.00	\N	\N	\N	Mg: 0.5 kg/ton, Ca: 3.57 kg/ton	\N
55	Leek	50.00	1.26	3.86	170.00	\N	\N	\N	Mg: 0.34 kg/ton, Ca: 1.72 kg/ton	\N
56	Rhubarb	25.00	5	8	125.00	\N	\N	\N	Mg: 1.6 kg/ton, Ca: 1.6 kg/ton	\N
57	Radicchio	20.00	1.5	6.5	120.00	\N	\N	\N	Mg: 2 kg/ton, Ca: 1 kg/ton	\N
58	Sugarloaf Radicchio	40.00	1.25	5.25	160.00	\N	\N	\N	Mg: 1.5 kg/ton, Ca: 0.45 kg/ton	\N
59	Red Beet	40.00	1.55	8	150.00	\N	\N	\N	Mg: 0.75 kg/ton, Ca: 1.08 kg/ton	\N
60	Radish (large)	40.00	1.25	3	120.00	\N	\N	\N	Mg: 0.5 kg/ton, Ca: 1.08 kg/ton	\N
61	Daikon Radish	50.00	1.2	3	140.00	\N	\N	\N	Mg: 0.5 kg/ton, Ca: 1 kg/ton	\N
62	Radish (small)	15.00	2	5.33	80.00	\N	\N	\N	Mg: 0.67 kg/ton, Ca: 2.87 kg/ton	\N
63	Sweet Corn	16.00	5.94	13.75	160.00	\N	\N	\N	Mg: 3.13 kg/ton, Ca: 9.38 kg/ton	\N
64	Lettuce (Batavia type)	40.00	1	4	80.00	\N	\N	\N	Mg: 0.38 kg/ton, Ca: 0.73 kg/ton	\N
65	Lettuce (crisphead)	32.50	1.23	4.92	115.00	\N	\N	\N	Mg: 0.49 kg/ton, Ca: 1.08 kg/ton	\N
66	Lettuce (soft-leaf)	40.00	1	4	80.00	\N	\N	\N	Mg: 0.38 kg/ton, Ca: 0.73 kg/ton	\N
67	Spinach	25.00	2.4	9	180.00	\N	\N	\N	Mg: 1.2 kg/ton, Ca: 3 kg/ton	\N
68	Bean (Pole Bean)	12.50	3.2	12	105.00	\N	\N	\N	Mg: 1.6 kg/ton, Ca: 16 kg/ton	Applies to both fresh beans (yield 12.5 t/ha) and dry grain (yield 2.5 t/ha)
69	Celery	50.00	1.6	8	200.00	\N	\N	\N	Mg: 0.5 kg/ton, Ca: 2.3 kg/ton	\N
70	Cabbage (stored, fresh)	50.00	1.3	5.6	240.00	\N	\N	\N	Mg: 0.8 kg/ton, Ca: 2.3 kg/ton	Also applies to Spring Cabbage (Zelje - spomladansko)
71	Cabbage (for processing)	80.00	1.31	5.6	320.00	\N	\N	\N	Mg: 0.8 kg/ton, Ca: 2.3 kg/ton	Also applies to Winter Cabbage (Zelje - zimsko)
72	Potato	40.00	1.4	6	120.00	\N	\N	\N	\N	\N
73	Eggplant	17.50	5.71	11.43	220.00	\N	\N	\N	Mg: 5.71 kg/ton, Ca: 11.43 kg/ton	\N
74	Cucumbers	50.00	0.833	2.333	70.00	\N	\N	\N	Mg: 0.233 kg/ton, Ca: 1.1 kg/ton	\N
75	Young Vines	1.00	7 (total kg/ha)	25 (total kg/ha)	30.00	0	30	30	\N	Yield range 0-2 t/ha; nutrient values fixed: PÔééOÔéů: 7 kg/ha, KÔééO: 25 kg/ha, N: 30 kg/ha
76	Alfalfa	10.00	1.3	6	0.00	0	0	0	\N	PÔééOÔéů and KÔééO aligned with Clover
77	Pasture	1.00	15 (total kg/ha)	20 (total kg/ha)	60.00	0	60	60	\N	Fixed yield 1 t/ha; PÔééOÔéů: 15 kg/ha, KÔééO: 20 kg/ha, N: 60 kg/ha
78	Carpet Grass Production	1.00	11 (total kg/ha)	20 (total kg/ha)	100.00	10	80	150	\N	Fixed yield 1 t/ha; PÔééOÔéů: 11 kg/ha, KÔééO: 20 kg/ha; merged with Grass
82	Sunflower	3.00	16	24	150.00	50	120	210	\N	\N
84	Watermelon	50.00	2	5	120.00	\N	\N	\N	\N	\N
85	Turnip	30.00	1.11	3.33	85.00	3.2	50	100	\N	\N
81	Meadow	10.00	1.53	3	100.00	0	100	100	\N	Merged Travnik (ko┼ínja), Trajni Travnik, and Ljulka (Travnik)
83	Plant nursery (vines)	1.00	14 (total kg/ha)	54 (total kg/ha)	30.00	0	30	30	\N	Fixed yield 1 t/ha; PÔééOÔéů: 14 kg/ha, KÔééO: 54 kg/ha, N: 30 kg/ha
80	Grass-clover mix	10.00	1.53	3	60.00	0	60	60	\N	\N
79	Clover-grass mix	10.00	1.8	2.6	40.00	0	40	40	\N	\N
\.


--
-- Data for Name: crop_protection_croatia; Type: TABLE DATA; Schema: public; Owner: -
--

COPY "public"."crop_protection_croatia" ("id", "product_name", "crop_hr", "crop_lat", "pest_hr", "pest_lat", "dose", "pre_harvest_interval", "remarks", "expiry", "source_file") FROM stdin;
\.


--
-- Data for Name: crop_technology; Type: TABLE DATA; Schema: public; Owner: -
--

COPY "public"."crop_technology" ("id", "crop_name", "stage", "action", "timing", "inputs", "notes") FROM stdin;
1	Soja	Plodored	Izbor preduseva	Pre setve	Bez	Preporu─Źeni predusevi: strna ┼żita, kukuruz, krompir. Izbegavati suncokret, uljanu repicu i monokulturu.
2	Soja	Priprema zemlji┼íta	Oranje i setvosprema	Jesen i prole─çe	Bez	Jesen: zaorati ┼żetvene ostatke. Kraj zime: zatvoriti brazdu za o─Źuvanje vlage. Prole─çe: setvosprema─Źem usitiniti zemlju, ─Źvrsta podloga, rastresit gornji sloj.
3	Soja	Inokulacija semena	Inokulacija	Pred setvo	Rhizobium japonicum (N-MAX ili inokulacija pre setve)	Ako nema kvr┼żica 1.5 mesec nakon setve, dodati azot (folijarno ili putem ─Ĺubrenja).
4	Soja	Setva	Setva	Ko se zemlji┼íte segreje na 12┬░C (kraj marta/pocetak aprila)	Seme: 25 kg/ha, sorta 'NS Maximus'	Dubina setve 4-5 cm, medvrstni razmak 70 cm (alternativno 12.5 cm, 25 cm ili 50 cm). Podesiti sejalicu prema deklaraciji semena.
5	Soja	Osnovno gnojenje	Gnojenje sa azotom	Tokom setve	N: 50 kg/ha	Za brzi start biljke i nicanje.
6	Soja	Pre nicanja	Aplikacija herbicida (PRE EM)	Nakon setve, pre nicanja	Herbicid za zemlji┼íte (doza prema preporuci)	Potrebne male padavine za aktivaciju; prskati pre klijanja soje.
7	Soja	Faza 3 trolistov	Me─Ĺuredna kultivacija (┼ípartanje)	Faza 3 trolistov i kasnije	Bez	Za razmak 50 cm ili 70 cm; sa─Źekati 1-2 nedelje nakon herbicidnog tretmana.
8	Soja	Faza 1-3 trolistov	Aplikacija herbicida (┼íirokolisni korovi)	Od prvih listova do pred cvetanje	Herbicid za ┼íirokolisne korove (split aplikacija, 10-15 dana razmaka)	Temperatura 15-25┬░C, prskati uve─Źe tokom vru─çina, izogibajte se de┼żju 48 ur.
9	Soja	Cvetenje i nalivanje mahuna	Navodnjavanje	Tokom cvetenja i nalivanja mahuna	400-450 mm vode za ciklus	Osigurati vlagu za dobru oplodnju cvetova i zametanje mahuna.
10	Soja	Cvetenje	Gnojenje z du┼íikom	Junij	N: 30 kg/ha (Urea)	Uporabite pred napovedanim de┼żjem.
11	Soja	Zametanje mahuna	Folijarna prihrana borom	Tokom zametanja mahuna	Bor (doza prema preporuci proizvo─Ĺa─Źa)	Poma┼że zametanju mahuna i formiranju zrna.
12	Soja	Letnji period	Suzbijanje ┼íteto─Źina	Tokom leta (pojava pau─Źinara ili leptira)	Akaricid za pau─Źinara, insekticid za Stri─Źkov ┼íarenjak (doza prema preporuci)	Pau─Źinar: tretirati ┼żari┼íta; Stri─Źkov ┼íarenjak: tretirati jaja i larve ako je zaraza jaka.
13	Soja	┼Żetev	┼Żetev	Septembar	Bez	Vla┼żnost zrn ~14 % (Pallador mo┼że 12 % zbog stay-green efekta), brzina kombajna ÔëĄ5 km/h (ÔëĄ3 km/h ako ima korova), heder nisko.
14	Suncokret	Plodored	Izbor preduseva	Pre setve	Bez	Preporu─Źeni predusevi: p┼íenica, strna ┼żita, kukuruz. Izbegavati soju, uljanu repicu, mahunarke.
15	Suncokret	Lju┼ítenje strni┼íta	Zaoravanje ostataka	Nakon ┼żetve preduseva	Bez	Dubina 10-15 cm, smanjuje gubitak vlage, pospe┼íuje razlaganje ostataka.
16	Suncokret	Osnovna obrada	Oranje	Jesen	Bez	Dubina 30-35 cm na te┼żim zemlji┼ítima, pli─çe na peskovitim; izbegavati prole─çno oranje.
17	Suncokret	Predsetvena priprema	Usitnjavanje i izravnavanje	10 dana pre setve	Bez	Dubina 4-6 cm, sa─Źuvati vlagu, minimizirati prolaze ma┼íina.
18	Suncokret	Setva	Setva	Kada je zemlji┼íte 8-10┬░C (april)	Seme: 55,000-65,000 biljaka/ha	Dubina 4-6 cm (zavisno od semena i zemlji┼íta), razmak 70 cm, tretirati seme protiv plamenja─Źe (oxathiapiprolin) i ┼íteto─Źina (tiakloprid).
19	Suncokret	Osnovno gnojenje	Gnojenje sa azotom	Jesen i prole─çe	N: 40-60 kg/ha (1/3 jesen, 1/3 prole─çe)	Za prinos 3 t/ha; prilagoditi analizi zemlji┼íta.
20	Suncokret	Pre nicanja	Aplikacija herbicida (PRE EM)	Nakon setve, pre nicanja	Herbicid (S-metalohlor, pendimetalin)	Potrebne padavine za aktivaciju; prskati pre nicanja.
21	Suncokret	Nakon nicanja	Razbijanje pokorice	Nakon obilnih ki┼ía	Bez	Koristiti rotacione kopa─Źice ili lake valjke za olak┼íano nicanje.
22	Suncokret	Faza 2-4 lista	Me─Ĺuredna kultivacija	Nakon nicanja	Bez	Razrahliti zemlji┼íte, posebno u su┼ínim godinama; kombinovati sa prihranjivanjem.
23	Suncokret	Faza 2-4 lista	Aplikacija herbicida (HT hibridi)	Od nicanja do cvetanja	Imazamox (Clearfield), tribenuron-metil (Express)	Za ┼íirokolisne korove; fluazifop-P-butil za uskolisne korove; izogibati se me┼íanju.
24	Suncokret	Faza 2-4 lista	Suzbijanje ┼íteto─Źina	Kod pojave ┼żi─Źara, pipa, va┼íi	Insekticid (tiakloprid, cipermetrin)	Tretirati seme ili zemlji┼íte; praviti kanale za pipe.
25	Suncokret	Prihranjivanje	Gnojenje sa azotom	Uz me─Ĺurednu kultivaciju	N: 40-60 kg/ha (1/3 prole─çe)	Koristiti nitratni ili amonija─Źni oblik; mogu─çe folijarno.
26	Suncokret	Formiranje glavice	Folijarna prihrana borom	Pre cvetanja	Bor (doza prema preporuci proizvo─Ĺa─Źa)	Spre─Źava nedostatak bora, posebno na plitkim zemlji┼ítima.
27	Suncokret	Formiranje glavice do cvetanja	Navodnjavanje	Kriti─Źna faza (40% potreba)	Prilagoditi koli─Źinu vode	Izbegavati prekomerno zalivanje zbog bolesti.
28	Suncokret	Cvetanje i sazrevanje	Suzbijanje volovoda	Tokom vegetacije	Imazamox (Clearfield hibridi)	Kombinovati sa plodoredom i otpornim hibridima.
29	Suncokret	Cvetanje i sazrevanje	Suzbijanje bolesti	Nakon o┼íte─çenja (grad, insekti)	Fungicid	Spre─Źava pojavu suve i sive trule┼żi na glavicama.
30	Suncokret	Sazrevanje	Suzbijanje ptica i ze─Źeva	Tokom zrenja	Repelenti, agrilaseri	Tretirati ivice parcele (npr. 2% kalijumov sapun protiv ze─Źeva).
31	Suncokret	┼Żetev	┼Żetev	Kada je vlaga 12-14%	Bez	Podesiti kombajn, izbegavati osipanje; dosu┼íiti ako je vlaga >14%.
32	Kukuruz	Plodored	Izbor preduseva	Pre setve	Bez	Preporu─Źeni predusevi: leguminoze, krompir, ┼íe─çerna repa, suncokret, uljana repica, strna ┼żita.
33	Kukuruz	Osnovna obrada	Oranje	Jesen, zima ili prole─çe	N: 100-150 kg/ha (urea)	Pre zaoravanja ┼żetvenih ostataka; dubina 30 cm; alternativno globoka obdelava (riper).
34	Kukuruz	Priprema za setvu	Usitnjavanje i izravnavanje	Prole─çe, blizu setve	Bez	Uni┼ítiti plevele; oru─Ĺe prilagoditi tipu tla (diskasta brana, setvosprema─Ź, vrtavkasta brana); izbegavati prefinu pripremu na finim tlima.
35	Kukuruz	Setva	Setva	Prole─çe (zemlji┼íte >10┬░C, april)	Seme (─Źisto─ça 99%, klijavost 93%)	Razmak 70 cm, dubina 4-7 cm; +10% na preporu─Źenu gustinu ┼żetve; gu┼í─çe na plodnim, re─Ĺe na siroma┼ínim tlima.
36	Kukuruz	Setva	Startno gnojenje	Tokom setve	N: 15-25 kg/ha (NPK 15-15-15 ili KAN)	Postaviti 5-8 cm pored, 3-5 cm ispod semena; max 30 kg/ha N iz NPK-a.
37	Kukuruz	Setva	Za┼ítita od ┼íteto─Źina	Tokom setve	Insekticid (Force 1.5 g ili tretirano seme)	Ako seme nije tretirano i sejalnica dozvoljava; rizik od struna ako se ne tretira.
38	Kukuruz	Pre nicanja	Razbijanje pokorice	Nakon setve, pre nicanja	Bez	Dubina <3 cm da se izbegne o┼íte─çenje klice; koristiti rotacionu kopa─Źicu.
39	Kukuruz	Nakon setve	Aplikacija herbicida	Do 4. lista koruze	Herbicid (Adengo)	Za trajne ┼íirokolisne plevele dodati Mustang (0.6 L/ha); za divji sirak dodati Equip (2.5 L/ha) u fazi 6. lista.
40	Kukuruz	Faza 4-5 listova	Me─Ĺuredna kultivacija	Faza 4-5 listova	Bez	Ostaviti 10-15 cm neobra─Ĺeno uz red; spre─Źava pokoricu, smanjuje gubitak vode.
41	Kukuruz	Faza 5 listova	Prihranjivanje	Pre ki┼íe	N: 90 kg/ha (300 kg KAN)	Klju─Źno za formiranje stor┼ża; privremena belina prihvatljiva.
42	Kukuruz	Faza 7-9 listova	Me─Ĺuredna kultivacija	Pre o┼íte─çenja useva	Bez	Druga kultivacija; uni┼ítava korove, provetrava zemlji┼íte.
43	Kukuruz	Faza 7-9 listova	Prihranjivanje	Uz me─Ĺurednu kultivaciju	N: 46 kg/ha (100 kg urea)	Za polnjenje zrna; ako nema okopavanja, dati 200 kg uree pre setve.
44	Kukuruz	Metli─Źanje i svilanje	Navodnjavanje	Pre metli─Źanja do nalivanja zrna	Prilagoditi koli─Źinu vode	Kriti─Źna faza za vodu; izbegavati su┼íu tokom oplodnje i nalivanja zrna.
45	Kukuruz	Berba	Berba u klipu	Kada je vlaga 14-30%	Bez	Skladi┼ítiti na ÔëĄ26% vlage; ventilacijom dosu┼íiti; gubici ÔëĄ2-3%.
46	P┼íenica	Osnovna obrada	Podrahljanje	Nakon ┼żetve preduseva (jesen)	Bez	Oranje nije neophodno; podrahljanje je dovoljno.
47	P┼íenica	Priprema za setvu	Usitnjavanje i izravnavanje	Jesen	Bez	Oru─Ĺe prilagoditi tipu tla (diskasta brana, setvosprema─Ź, vrtavkasta brana); vrtavkasta brana dobra ali spora.
48	P┼íenica	Setva	Setva	Sredina oktobra do novembra	Seme (prema preporuci)	+10% na preporu─Źenu gustinu ┼żetve; +10% posle 25. oktobra, +20% posle 1. novembra; seme obavezno tretirano fungicidom.
49	P┼íenica	Setva	Osnovno gnojenje	Jesen (tokom setve)	N: 30 kg/ha (KAN)	Ako je predusev kukuruz, 60 kg/ha N; ako je soja, izostaviti N.
50	P┼íenica	Setva	Startno gnojenje	Tokom setve	N: 20% od ukupnog N (KAN)	Ako sejalnica dozvoljava; ostatak povrh tla; manje klju─Źno nego za kukuruz.
51	P┼íenica	Jesen/zima	Aplikacija herbicida	Jesen (3 lista) ili rano prole─çe	Herbicid (Alister NEW 1 L/ha)	No─ç >0┬░C, dan >10┬░C; alternativno Hussar Star + 1 L/ha Mero u prole─çe pre kolen─Źenja.
52	P┼íenica	Prekoljen─Źanje	Dognojevanje	Prelaz zima/prole─çe	N: 67 kg/ha (250 kg KAN)	Dan >8┬░C, no─ç >0┬░C; pred ki┼íu (10-20 mm); ako je predusev kukuruz, +15 kg N/ha.
53	P┼íenica	Kolen─Źenje	Fungicid (prvo tretiranje)	Po─Źetak kolen─Źenja (ili ranije)	Duett Ultra, Delaro Forte ili Amistar	Ako se pojave znaci bolesti, tretirati ranije; ┼ítiti donje listove.
54	P┼íenica	Kolen─Źenje	Rastni regulator	Izme─Ĺu 1. i 2. kolenca	Moddus (Syngenta)	Smanjuje rizik od poleganja.
55	P┼íenica	Kolen─Źenje	Dognojevanje	Po─Źetak kolen─Źenja (1. kolence)	N: 67 kg/ha (250 kg KAN)	Pred ki┼íu; ako je predusev kukuruz, +15 kg N/ha; ako nema ki┼íe, folijarno N privremeno.
56	P┼íenica	Zastavica	Fungicid (drugo tretiranje)	Pojava zastavice	Elatus Era ili Ascra	┼átiti zastavicu (45% prinosa); tretirati 20-30 dana nakon prvog tretiranja.
57	P┼íenica	Zastavica	Suzbijanje ┼íteto─Źina	Pojava ┼żitnog strga─Źa	Insekticid (Decis ili Karate Zeon)	Tretirati pri prvim znacima ┼ítete; mo┼żda vi┼íe tretmana.
58	P┼íenica	Klasenje	Dognojevanje	Tokom klasenja	N: 27 kg/ha (100 kg KAN)	Pred ki┼íu; osigurava N za zrenje zrna.
59	P┼íenica	Cvetenje	Fungicid (tre─çe tretiranje)	Tokom cvetenja u klasu	Prosaro	Preporu─Źeno ─Źak i u su┼ínim uslovima; ┼ítiti klas (20% prinosa).
60	P┼íenica	┼Żetva	┼Żetva	Kada je vlaga 14-15%	Bez	Berba u punoj zrelosti; su┼íiti ako je vlaga ve─ça.
\.


--
-- Data for Name: farm_machinery; Type: TABLE DATA; Schema: public; Owner: -
--

COPY "public"."farm_machinery" ("id", "farm_id", "category", "subcategory", "year_of_production", "year_of_purchase", "purchase_price", "producer", "model", "horsepower_tractor", "has_navigation", "navigation_producer", "navigation_model", "navigation_reads_maps", "navigation_reads_maps_producer", "navigation_reads_maps_model", "horsepower_harvester", "harvesting_width_cereals", "harvesting_width_maize", "harvesting_width_sunflower", "can_map_yield", "sowing_units_maize", "can_add_fertilizer_maize", "can_add_microgranules_maize", "distance_between_units_cm", "distance_variable", "can_read_prescription_maps_maize", "distance_between_rows_cereals", "can_add_fertilizer_cereals", "can_add_microgranules_cereals", "width_sowing_cereals", "can_read_prescription_maps_cereals", "plough_bodies", "plough_size", "podriva─Ź_width", "sjetvosprema─Ź_producer", "sjetvosprema─Ź_model", "sjetvosprema─Ź_width", "rotobrana_width", "fertilizer_spreader_producer", "fertilizer_spreader_model", "can_read_prescription_maps_spreader", "can_adjust_quantity_from_cabin", "cultivation_width_maize", "can_add_fertilizer_cultivation", "sprayer_width", "has_section_control", "can_read_prescription_maps_sprayer", "notes") FROM stdin;
\.


--
-- Data for Name: farm_organic_fertilizers; Type: TABLE DATA; Schema: public; Owner: -
--

COPY "public"."farm_organic_fertilizers" ("id", "farm_id", "fertilizer_id", "npk_composition", "analysis_date", "notes") FROM stdin;
\.


--
-- Data for Name: farmers; Type: TABLE DATA; Schema: public; Owner: -
--

COPY "public"."farmers" ("id", "state_farm_number", "farm_name", "manager_name", "manager_last_name", "street_and_no", "village", "postal_code", "city", "country", "vat_no", "email", "phone", "wa_phone_number", "notes") FROM stdin;
1	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	+38641348050	\N
2	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	+38651322019	\N
3	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	+4915156006708	\N
4	100337558	KMETIJA VRZEL	BLA┼Ż	VRZEL	Turjanci 25A	\N	9252	Radenci	Slovenia	SI58625887	kmetija.vrzel@gmail.com	38631775817	+38631775817	\N
\.


--
-- Data for Name: fertilizers; Type: TABLE DATA; Schema: public; Owner: -
--

COPY "public"."fertilizers" ("id", "product_name", "npk_composition", "notes", "common_name", "is_organic", "is_calcification", "ca_content", "country", "producer", "formulations", "granulation") FROM stdin;
1	Superphosphate	0:46:0	P-only fertilizer	\N	f	f	\N	Croatia	\N	\N	\N
2	KCl	0:0:60	K-only fertilizer	\N	f	f	\N	Croatia	\N	\N	\N
3	MAP	12:52:0	Monoammonium Phosphate	\N	f	f	\N	Croatia	\N	\N	\N
4	DAP	18:46:0	Diammonium Phosphate	\N	f	f	\N	Croatia	\N	\N	\N
5	NPK 7-20-30	7:20:30	Common NPK fertilizer	sedmica	f	f	\N	Croatia	\N	\N	\N
6	NPK 15-15-15	15:15:15	Balanced NPK fertilizer	petnajstica	f	f	\N	Croatia	\N	\N	\N
7	Cattle Slurry	4:2:8	Standard values, farm-specific analysis can override	\N	t	f	\N	Croatia	\N	\N	\N
8	Poultry Manure	3:2.5:2	Standard values, farm-specific analysis can override	\N	t	f	\N	Croatia	\N	\N	\N
9	CaCO3	0:0:0	Calcium Carbonate for calcification	\N	f	t	40	Croatia	\N	\N	\N
10	CaO	0:0:0	Calcium Oxide, multiply quantities by 2 for CaCO3 equivalence	\N	f	t	71	Croatia	\N	\N	\N
\.


--
-- Data for Name: fertilizing_plans; Type: TABLE DATA; Schema: public; Owner: -
--

COPY "public"."fertilizing_plans" ("field_id", "year", "crop_name", "p2o5_kg_ha", "p2o5_kg_field", "k2o_kg_ha", "k2o_kg_field", "n_kg_ha", "n_kg_field", "fertilizer_recommendation") FROM stdin;
1	2025	Travnik	7.65	1.74	15	3.41	21.99	5	Superfosfat: 40 kg (176 kg/ha), Kalijev klorid: 10 kg (44 kg/ha)
1	2026	Travnik	0	0	15	3.41	21.99	5	Kalijev klorid: 10 kg (44 kg/ha)
1	2027	Koruza za zrnje	0	0	45.03	10.24	153.91	35	Kalijev klorid: 20 kg (88 kg/ha)
1	2028	Tritikala	50.04	11.38	9.41	2.14	109.94	25	Superfosfat: 20 kg (88 kg/ha), Kalijev klorid: 10 kg (44 kg/ha)
1	2029	Lucerna	11.26	2.56	0	0	0	0	Superfosfat: 10 kg (44 kg/ha)
2	2025	Je─Źmen/TDM/Lucerna	32.78	104.4	16.52	52.6	23.55	75	Superfosfat: 230 kg (72 kg/ha), Kalijev klorid: 90 kg (28 kg/ha)
2	2026	Koruza za zrnje	315	1003.11	150.39	478.97	155.38	495	Superfosfat: 2180 kg (685 kg/ha), Kalijev klorid: 800 kg (251 kg/ha)
2	2027	Tritikala	197.03	627.44	36.89	117.48	119.33	380	Superfosfat: 1360 kg (427 kg/ha), Kalijev klorid: 200 kg (63 kg/ha)
2	2028	Lucerna	43.73	139.28	63.55	202.41	0	0	Superfosfat: 300 kg (94 kg/ha), Kalijev klorid: 340 kg (107 kg/ha)
2	2029	Lucerna	43.73	139.28	63.55	202.41	0	0	Superfosfat: 300 kg (94 kg/ha), Kalijev klorid: 340 kg (107 kg/ha)
3	2025	Grozdje za vino	8.75	6.67	31.25	23.81	32.81	25	Superfosfat: 20 kg (26 kg/ha), Kalijev sulfat: 50 kg (66 kg/ha)
3	2026	Grozdje za vino	0	0	31.25	23.81	32.81	25	Kalijev sulfat: 50 kg (66 kg/ha)
3	2027	Grozdje za vino	0	0	7.01	5.34	32.81	25	Kalijev sulfat: 30 kg (39 kg/ha)
3	2028	Grozdje za vino	4	3.05	0	0	32.81	25	Superfosfat: 10 kg (13 kg/ha)
3	2029	Grozdje za vino	6	4.57	21.01	16.01	32.81	25	Superfosfat: 10 kg (13 kg/ha), Kalijev sulfat: 30 kg (39 kg/ha)
\.


--
-- Data for Name: field_crops; Type: TABLE DATA; Schema: public; Owner: -
--

COPY "public"."field_crops" ("field_id", "start_year_int", "crop_name", "variety", "expected_yield_t_ha", "start_date", "end_date") FROM stdin;
1	2025	Travnik	\N	4	2025-04-01	\N
1	2026	Travnik	\N	4	2026-04-01	\N
1	2027	Koruza za zrnje	NS 4020	9	2027-04-01	\N
1	2028	Tritikala	Triton	5	2028-04-01	\N
1	2029	Lucerna	\N	5	2029-04-01	\N
2	2025	Je─Źmen/TDM/Lucerna	Barun/NULL/NULL	2	2025-04-01	\N
2	2026	Koruza za zrnje	NS 4020	9	2026-04-01	\N
2	2027	Tritikala	Triton	5	2027-04-01	\N
2	2028	Lucerna	\N	5	2028-04-01	\N
2	2029	Lucerna	\N	5	2029-04-01	\N
3	2026	Grozdje za vino	Merlot	0	2026-04-01	\N
3	2027	Grozdje za vino	Merlot	2	2027-04-01	\N
3	2028	Grozdje za vino	Merlot	4	2028-04-01	\N
3	2029	Grozdje za vino	Merlot	6	2029-04-01	\N
3	2025	Grozdje za vino	Merlot	\N	2025-04-01	\N
1	2024	Corn (silage)	\N	\N	2024-05-10	\N
2	2024	Corn (silage)	\N	\N	2024-05-10	\N
3	2024	Corn (silage)	\N	\N	2024-05-10	\N
4	2024	Corn (silage)	\N	\N	2024-05-10	\N
5	2024	Corn (silage)	\N	\N	2024-05-10	\N
20	2024	Corn (silage)	\N	\N	2024-05-10	\N
29	2024	Corn (silage)	\N	\N	2024-05-10	\N
34	2024	Corn (silage)	\N	\N	2024-05-10	\N
35	2024	Corn (silage)	\N	\N	2024-05-10	\N
39	2024	Corn (silage)	\N	\N	2024-05-10	\N
6	2024	Wheat (grain, straw left)	\N	\N	2023-10-08	\N
7	2024	Wheat (grain, straw left)	\N	\N	2023-10-08	\N
8	2024	Wheat (grain, straw left)	\N	\N	2023-10-08	\N
9	2024	Wheat (grain, straw left)	\N	\N	2023-10-08	\N
10	2024	Wheat (grain, straw left)	\N	\N	2023-10-08	\N
11	2024	Wheat (grain, straw left)	\N	\N	2023-10-08	\N
12	2024	Wheat (grain, straw left)	\N	\N	2023-10-08	\N
6	2024	Wheat (grain, straw left)	\N	\N	2023-10-08	\N
7	2024	Wheat (grain, straw left)	\N	\N	2023-10-08	\N
8	2024	Wheat (grain, straw left)	\N	\N	2023-10-08	\N
9	2024	Wheat (grain, straw left)	\N	\N	2023-10-08	\N
10	2024	Wheat (grain, straw left)	\N	\N	2023-10-08	\N
11	2024	Wheat (grain, straw left)	\N	\N	2023-10-08	\N
12	2024	Wheat (grain, straw left)	\N	\N	2023-10-08	\N
6	2024	Wheat (grain, straw left)	\N	\N	2023-10-01	\N
7	2024	Wheat (grain, straw left)	\N	\N	2023-10-01	\N
8	2024	Wheat (grain, straw left)	\N	\N	2023-10-01	\N
9	2024	Wheat (grain, straw left)	\N	\N	2023-10-01	\N
10	2024	Wheat (grain, straw left)	\N	\N	2023-10-01	\N
11	2024	Wheat (grain, straw left)	\N	\N	2023-10-01	\N
12	2024	Wheat (grain, straw left)	\N	\N	2023-10-01	\N
\.


--
-- Data for Name: field_soil_data; Type: TABLE DATA; Schema: public; Owner: -
--

COPY "public"."field_soil_data" ("field_id", "analysis_date", "ph", "p2o5_mg_100g", "k2o_mg_100g", "organic_matter_percent", "analysis_method", "analysis_institution") FROM stdin;
3	2025-01-01	5.8	10	15	1.5	AL	Agricultural Institute of Slovenia
1	2025-05-14	6.5	6	17	3	AL	Agricultural Institute of Slovenia
2	2025-05-14	6.8	3	16	2.8	AL	Agricultural Institute of Slovenia
3	2025-05-14	7	6	15	2.5	AL	Agricultural Institute of Slovenia
2	2025-01-01	6.5	15	25	2	AL	Lab XYZ
\.


--
-- Data for Name: fields; Type: TABLE DATA; Schema: public; Owner: -
--

COPY "public"."fields" ("id", "farmer_id", "field_name", "area_ha", "latitude", "longitude", "blok_id", "raba", "nup_m2", "povprecna_nmv", "povprecna_ekspozicija", "povprecni_naklon", "notes", "country", "field_state_id") FROM stdin;
1	1	LIJAK 1	0.2274	45.8145	15.9667	\N	\N	\N	\N	\N	\N	\N	Croatia	\N
2	1	MARJUTINO	3.1844	45.815	15.967	\N	\N	\N	\N	\N	\N	\N	Croatia	\N
3	1	PAV┼á─îEVO	0.762	45.8155	15.9675	\N	\N	\N	\N	\N	\N	\N	Croatia	\N
4	4	DOMA─îE - 4	0.1022	\N	\N	11471212	1222(SD) Ekstenzivni sadovnjak	1022	243.84	30┬░	12.7	\N	Slovenia	965826
5	4	DOMA─îE - 2	0.8276	\N	\N	11471219	1100(N) Njiva	8276	230.416	84┬░	4.4	\N	Slovenia	968135
6	4	RAUTAR	0.4935	\N	\N	11964708	1100(N) Njiva	4935	223.27	57┬░	1.8	\N	Slovenia	968138
7	4	KAPELA-D	9.6123	\N	\N	11471201	1100(N) Njiva	96123	215.705	64┬░	2.3	\N	Slovenia	968146
8	4	KAPELA-L	11.4827	\N	\N	11471200	1100(N) Njiva	114827	213.596	58┬░	1.6	\N	Slovenia	968503
9	4	ZA HLEVI	1.9268	\N	\N	11471206	1100(N) Njiva	19268	204.733	15┬░	1.2	\N	Slovenia	968506
10	4	PETOVAR-1	3.8298	\N	\N	11471203	1100(N) Njiva	38298	195.624	119┬░	0.6	\N	Slovenia	968508
11	4	VRTINA - L	0.6326	\N	\N	11471221	1100(N) Njiva	6326	195.426	224┬░	0.5	\N	Slovenia	968511
12	4	VRTINA - D	0.858	\N	\N	11471217	1100(N) Njiva	8580	195.193	159┬░	0.6	\N	Slovenia	968513
13	4	ZORKO - 2	1.1214	\N	\N	11471214	1100(N) Njiva	11214	194.45	176┬░	0.5	\N	Slovenia	968514
14	4	ZORKO - 3	0.3035	\N	\N	11471228	1100(N) Njiva	3035	194.021	89┬░	0.7	\N	Slovenia	968516
15	4	MOTA	15.0537	\N	\N	11471198	1100(N) Njiva	150537	204.082	91┬░	1.1	\N	Slovenia	968866
16	4	ZORKO - 8	0.1968	\N	\N	11471230	1100(N) Njiva	1968	194.016	302┬░	0.9	\N	Slovenia	968870
17	4	ZORKO - 1	1.3815	\N	\N	11471210	1100(N) Njiva	13815	199.667	60┬░	0.7	\N	Slovenia	968873
18	4	ZORKO - 4	0.9657	\N	\N	11471215	1100(N) Njiva	9657	193.548	211┬░	1	\N	Slovenia	968874
19	4	ZORKO - 7	0.3295	\N	\N	11882581	1100(N) Njiva	3295	193.865	216┬░	0.8	\N	Slovenia	968877
20	4	HRASTJE	12.5821	\N	\N	11471199	1100(N) Njiva	125821	195.594	59┬░	1	\N	Slovenia	968883
21	4	DOMA─îE	0.0759	\N	\N	11471231	1300(T) Trajni travnik	759	237.365	1┬░	12.8	\N	Slovenia	969182
22	4	LETMER┼á─îAK	1.3676	\N	\N	12040810	1100(N) Njiva	13676	178.383	75┬░	0.6	\N	Slovenia	989929
23	4	VRLEKOV STRAMI─î	0.3898	\N	\N	11926357	1300(T) Trajni travnik	3898	194.729	144┬░	0.9	\N	Slovenia	1024589
24	4	POD BREGOM STRAMI─î	0.1582	\N	\N	11926358	1300(T) Trajni travnik	1582	193.609	41┬░	2.1	\N	Slovenia	1024592
25	4	BUDJA 3	1.3732	\N	\N	11882589	1100(N) Njiva	13732	212.166	73┬░	1.5	\N	Slovenia	1025673
26	4	BUDJA 4	0.7322	\N	\N	11882591	1100(N) Njiva	7322	199.635	188┬░	0.9	\N	Slovenia	1025674
27	4	BUDJA 1	0.5174	\N	\N	11882592	1100(N) Njiva	5174	211.94	63┬░	0.7	\N	Slovenia	1031453
28	4	BERDEN 5	0.3964	\N	\N	11882582	1100(N) Njiva	3964	194.363	324┬░	0.7	\N	Slovenia	1046655
29	4	STRAMI─î 2	1.8751	\N	\N	11910042	1100(N) Njiva	18751	207.584	68┬░	1.4	\N	Slovenia	1054238
30	4	STRAMI─î 1	1.3177	\N	\N	11910043	1100(N) Njiva	13177	200.745	359┬░	0.7	\N	Slovenia	1054244
31	4	BUDJA 2	1.0703	\N	\N	11882590	1100(N) Njiva	10703	213.966	19┬░	0.7	\N	Slovenia	1072338
32	4	GOMBOC - 2	0.5891	\N	\N	11471222	1100(N) Njiva	5891	204.584	36┬░	1.1	\N	Slovenia	1187522
33	4	GOMBOC - 1	3.4447	\N	\N	11471205	1100(N) Njiva	34447	198.125	97┬░	0.8	\N	Slovenia	1187523
34	4	KRI┼ŻANI─î - 1	4.0964	\N	\N	11471204	1100(N) Njiva	40964	207.839	44┬░	1.3	\N	Slovenia	1235182
35	4	SADOVNJAK	3.4853	\N	\N	11888441	1100(N) Njiva	34853	256.343	118┬░	4.3	\N	Slovenia	1697469
36	4	PUK┼áI─î 1	0.5613	\N	\N	11471223	1100(N) Njiva	5613	195.491	225┬░	0.6	\N	Slovenia	2476082
37	4	PUK┼áI─î-3	0.1769	\N	\N	11471232	1100(N) Njiva	1769	194.322	226┬░	0.8	\N	Slovenia	2476083
38	4	DOMA─îE - 1	1.401	\N	\N	11471209	1100(N) Njiva	14010	217.704	66┬░	2	\N	Slovenia	3404431
39	4	PA┼áNIK	5.8099	\N	\N	11471202	1100(N) Njiva	58099	205.919	27┬░	1	\N	Slovenia	3404801
40	4	ZORKO - 6	0.4956	\N	\N	11471226	1100(N) Njiva	4956	194.009	153┬░	0.8	\N	Slovenia	3405474
41	4	ZORKO - 5	0.3328	\N	\N	11471227	1100(N) Njiva	3328	194.213	150┬░	0.9	\N	Slovenia	3405549
42	4	DEPONIJA	2.6518	\N	\N	11471208	1100(N) Njiva	26518	196.06	60┬░	0.8	\N	Slovenia	3405956
43	4	KUMP STRAMI─î	0.5783	\N	\N	11926356	1300(T) Trajni travnik	5783	193.803	235┬░	1.9	\N	Slovenia	3540064
44	4	VRLEKOV 2 STRAMI─î	0.1409	\N	\N	11926359	1300(T) Trajni travnik	1409	194.082	181┬░	1.1	\N	Slovenia	3540498
45	4	POD BREGOM_1 STRAMI─î	0.3816	\N	\N	11882583	1300(T) Trajni travnik	3816	193.449	213┬░	1	\N	Slovenia	4598437
46	4	DOMA─îE - 4_1	0.0441	\N	\N	11888442	1222(SD) Ekstenzivni sadovnjak	441	251.93	67┬░	12.4	\N	Slovenia	4599564
47	4	PUK┼áI─î - 2	0.9291	\N	\N	11471216	1100(N) Njiva	9291	194.912	163┬░	0.7	\N	Slovenia	4699626
48	4	ZA HLEVI_3	1.9466	\N	\N	11471207	1100(N) Njiva	19466	207.443	13┬░	1.2	\N	Slovenia	5318096
49	4	BELAK	0.31	\N	\N	11982438	1300(T) Trajni travnik	3100	194.906	190┬░	1	\N	Slovenia	5396819
50	4	OPLETAR	0.1303	\N	\N	12047735	1100(N) Njiva	1303	195.408	236┬░	0.8	\N	Slovenia	5396855
51	4	GOMILICE 1	0.8649	\N	\N	11964707	1100(N) Njiva	8649	198.317	88┬░	1	\N	Slovenia	6212747
52	4	VRZEL	0.4171	\N	\N	11471203	1300(T) Trajni travnik	4171	195.494	181┬░	0.4	\N	Slovenia	6253511
53	4	DOMA─îE - 4_2	0.0184	\N	\N	11983328	1300(T) Trajni travnik	184	240.3	3┬░	15.4	\N	Slovenia	6261273
\.


--
-- Data for Name: growth_stage_reports; Type: TABLE DATA; Schema: public; Owner: -
--

COPY "public"."growth_stage_reports" ("id", "field_id", "crop_name", "variety", "growth_stage", "date_reported", "farmer_id", "reported_via", "notes") FROM stdin;
1	1	Soja	NS Maximus	Faza 1-3 trolistov	2025-05-15	1	WhatsApp	Reported during sunny weather
\.


--
-- Data for Name: incoming_messages; Type: TABLE DATA; Schema: public; Owner: -
--

COPY "public"."incoming_messages" ("id", "farmer_id", "phone_number", "message_text", "timestamp", "role") FROM stdin;
293	3	+4915156006708	Hast du nix Anderes zu tun als diese bloede bots mit deine Fragen zu ueberfordern?	2025-05-19 22:04:58.181812	agronomist
295	3	+4915156006708	Ich m├Âchte eine Antwort ohne Template!	2025-05-19 22:05:32	user
297	3	+4915156006708	Zur zeit hat unser haupt IT Nerd keine Zeit um das zu wechseln, koennte mann aber so was tun. 	2025-05-19 22:07:09.32085	agronomist
301	3	+4915156006708	Yes	2025-05-19 22:13:40	user
303	3	+4915156006708	 Dein deutsch wird immer besser. Dein aber nicht: "deutsch" sollte "Deutsch" geschrieben sein..	2025-05-19 22:16:19.7477	agronomist
306	3	+4915156006708	Question: Can you tell me your expected yield for this crop in tons per hectare?	2025-05-19 22:17:27.121912	system
212	3	+4915156006708	Yes	2025-05-18 17:02:38	user
308	3	+4915156006708	Peter saying: you are getting many messages at once as I am not confirming them and then I confirm all at once.	2025-05-19 22:19:50.094697	agronomist
13	2	+38651322019	Trte mi je prijela peronospora, s ─Źim naj po┼ípricam?	2025-05-17 19:34:36	user
14	2	+38651322019	Mi prevedes v slovenscino?	2025-05-17 19:35:06	user
15	2	+38651322019	Trte mi je prijela peronospora, s ─Źim naj po┼ípricam?	2025-05-17 19:28:22	user
19	3	+4915156006708	Kannst du mir mit einer landwirtschaftlichen Frage helfen?	2025-05-15 11:06:58	user
20	2	+38651322019	Kaksno je vreme v logatcu?	2025-05-15 10:47:57	user
45	3	+4915156006708	Is someone there?	2025-05-17 15:29:51	user
51	3	+4915156006708	No	2025-05-18 11:14:02	user
216	2	+38651322019	Samo test	2025-05-18 19:44:25.647415	agronomist
218	3	+4915156006708	I received the message	2025-05-18 19:45:05	user
220	3	+4915156006708	Question: Can you tell me your expected yield for this crop in tons per hectare?	2025-05-18 19:54:22.501421	system
222	3	+4915156006708	Question: Kannst du mir deine erwartete Ernte f├╝r diese Kultur in Tonnen pro Hektar mitteilen?	2025-05-18 19:54:26.400581	system
224	3	+4915156006708	Question: Can you tell me your expected yield for this crop in tons per hectare?	2025-05-18 19:54:30.601359	system
226	3	+4915156006708	Question: Can you tell me if a soil analysis was done on your fields? (Yes/No)	2025-05-18 20:00:17.873581	system
228	3	+4915156006708	Question: Do you have any fertilizer in stock? (Yes/No)	2025-05-18 20:01:33.639381	system
230	3	+4915156006708	Test 20:12	2025-05-18 20:12:31.359329	agronomist
309	3	+4915156006708	I see	2025-05-19 22:20:14	user
313	3	+4915156006708	Question: Can you tell me your expected yield for this crop in tons per hectare?	2025-05-19 22:25:28.778428	system
242	3	+4915156006708	Hallo :)	2025-05-15 20:55:34	user
332	1	+38641348050	How much potassium should I use for my vineyard?	2025-05-19 22:52:06	user
334	1	+38641348050	How much potassium shoul I use in my vineyard?	2025-05-18 11:29:23	user
336	1	+38641348050	How much potassium should I use?	2025-05-19 19:19:53	user
337	1	+38641348050	Question: Please provide a numerical value for the expected yield (e.g., 10 tons).	2025-05-20 08:08:00.357423	system
340	3	+4915156006708	noch ein test	2025-05-15 20:55:20	user
342	1	+38641348050	No	2025-05-18 11:29:40	user
344	1	+38641348050	5	2025-05-18 11:30:02	user
346	1	+38641348050	How much potassium should I use?	2025-05-19 16:46:12	user
347	1	+38641348050	Question: Please answer with 'Yes' or 'No': Do you have any fertilizer in stock?	2025-05-20 13:11:50.532516	system
349	1	+38641348050	Question: Please answer with 'Yes' or 'No': Do you have any fertilizer in stock?	2025-05-20 13:46:23.060972	system
351	1	+38641348050	No	2025-05-18 11:30:21	user
352	1	+38641348050	How much potassium should I use?	2025-05-19 18:44:25	user
354	1	+38641348050	How much potassium should I use?	2025-05-19 19:02:58	user
357	3	+4915156006708	Question: Please provide a numerical value for the expected yield (e.g., 10 tons).	2025-05-20 23:20:26.289797	system
359	3	+4915156006708	Question: Please provide a numerical value for the expected yield (e.g., 10 tons).	2025-05-21 00:08:43.287228	system
287	3	+4915156006708	Any advice for my field?	2025-05-19 22:03:01	user
291	3	+4915156006708	Question: Was a soil analysis done on your fields? (Yes/No)	2025-05-19 22:03:47.692884	system
298	3	+4915156006708	Question: Was a soil analysis done on your fields? (Yes/No)	2025-05-19 22:08:12.34099	system
300	3	+4915156006708	Yea	2025-05-19 22:13:37	user
302	3	+4915156006708	Dein deutsch wird immer besser	2025-05-19 22:14:07	user
304	3	+4915156006708	Question: Can you tell me your expected yield for this crop in tons per hectare?	2025-05-19 22:17:22.405189	system
305	3	+4915156006708	Question: Can you tell me your expected yield for this crop in tons per hectare?	2025-05-19 22:17:24.006105	system
213	3	+4915156006708	Aha! Jetzt wurde aus Peter dem. cleveren Weinbauern ein IT Nerd :)	2025-05-18 17:08:50	user
135	3	+4915156006708	Test	2025-05-17 15:30:05	user
215	3	+4915156006708	This is just a test	2025-05-18 19:39:16.901952	agronomist
307	3	+4915156006708	5	2025-05-19 22:17:47	user
219	3	+4915156006708	How much potassium should I use on my larger field?	2025-05-18 19:48:42	user
221	3	+4915156006708	Question: Can you tell me your expected yield for this crop in tons per hectare?	2025-05-18 19:54:24.878246	system
225	3	+4915156006708	7	2025-05-18 19:58:17	user
227	3	+4915156006708	No	2025-05-18 20:01:16	user
229	3	+4915156006708	No	2025-05-18 20:02:43	user
231	3	+4915156006708	Question: Was a soil analysis done on your fields? (Yes/No)	2025-05-18 20:12:50.104804	system
312	3	+4915156006708	Question: Do you have any fertilizer in stock? (Yes/No)	2025-05-19 22:25:26.975635	system
239	3	+4915156006708	What is your advice for today?	2025-05-19 08:26:49	user
333	1	+38641348050	Question: Can you tell me your expected yield for this crop in tons per hectare?	2025-05-19 22:52:07.179329	system
335	1	+38641348050	Question: Please provide a numerical value for the expected yield (e.g., 10 tons).	2025-05-20 07:40:48.628065	system
338	3	+4915156006708	Test99	2025-05-15 14:41:44	user
339	3	+4915156006708	Question: Can you tell me your expected yield for this crop in tons per hectare?	2025-05-20 08:43:19.001773	system
341	3	+4915156006708	Question: Please provide a numerical value for the expected yield (e.g., 10 tons).	2025-05-20 11:43:04.892864	system
343	1	+38641348050	Question: Please provide a numerical value for the expected yield (e.g., 10 tons).	2025-05-20 12:51:18.202583	system
345	1	+38641348050	Question: Was a soil analysis done on your fields? (Yes/No)	2025-05-20 12:54:58.385402	system
348	1	+38641348050	How much potassium should I use?	2025-05-19 19:03:28	user
350	1	+38641348050	No	2025-05-18 11:30:21	user
353	1	+38641348050	How much potassium should I use?	2025-05-19 19:02:58	user
355	1	+38641348050	How much potassium should I use?	2025-05-19 19:02:58	user
356	3	+4915156006708	Test-1000	2025-05-15 18:08:35	user
358	3	+4915156006708	Test	2025-05-15 13:59:22	user
\.


--
-- Data for Name: inventory; Type: TABLE DATA; Schema: public; Owner: -
--

COPY "public"."inventory" ("id", "farmer_id", "material_id", "quantity", "unit", "purchase_date", "purchase_price", "source_invoice_id", "notes") FROM stdin;
1	4	1	1925	kg	2023-10-20	0.7276704	1	Invoice: 26RA-260526/2023, Supplier: KZ RADGONA Z.O.O.
2	4	2	440	kg	2023-10-20	0.6575328	1	Invoice: 26RA-260526/2023, Supplier: KZ RADGONA Z.O.O.
3	4	3	6000	kg	2023-11-03	0.78	2	Invoice: 246558, Supplier: RAIFFEISEN AGRO TRGOVINA D.O.O.
4	4	4	2400	kg	2023-11-03	0.77	2	Invoice: 246558, Supplier: RAIFFEISEN AGRO TRGOVINA D.O.O.
5	4	5	24000	kg	2024-02-21	0.536986	3	Invoice: 223018, Supplier: RAIFFEISEN AGRO TRGOVINA D.O.O.
6	4	6	2	L	2024-03-31	67.6821888	4	Invoice: 26RA-260144/2024, Supplier: KZ RADGONA Z.O.O.
7	4	7	0.1	kg	2024-03-31	395.39721599999996	4	Invoice: 26RA-260144/2024, Supplier: KZ RADGONA Z.O.O.
8	4	8	24	L	2024-03-31	77.2173528	4	Invoice: 26RA-260144/2024, Supplier: KZ RADGONA Z.O.O.
9	4	9	60	L	2024-03-31	33.64942440000001	4	Invoice: 26RA-260144/2024, Supplier: KZ RADGONA Z.O.O.
10	4	10	3	kg	2024-03-31	118.122374	4	Invoice: 26RA-260144/2024, Supplier: KZ RADGONA Z.O.O.
11	4	11	44	L	2024-03-31	5.4082148000000005	4	Invoice: 26RA-260144/2024, Supplier: KZ RADGONA Z.O.O.
12	4	10	9	kg	2024-03-31	125.44779399999999	4	Invoice: 26RA-260144/2024, Supplier: KZ RADGONA Z.O.O.
13	4	12	15000	kg	2024-03-31	0.4753534272	5	Invoice: 26RA-26009872024, Supplier: KZ RADGONA Z.O.O.
14	4	13	20	L	2024-03-31	9.731510400000001	6	Invoice: 26RA-260100/2024, Supplier: KZ RADGONA Z.O.O.
15	4	14	95	L	2024-03-31	21.89114688	7	Invoice: 26RA-26009972024, Supplier: KZ RADGONA Z.O.O.
16	4	15	10500	kg	2024-03-31	0.3256360045714286	8	Invoice: 26RA-260097/2024, Supplier: KZ RADGONA Z.O.O.
17	4	16	175	mk	2024-03-31	2.9352694279999993	9	Invoice: 26RA-260091/2024, Supplier: KZ RADGONA Z.O.O.
18	4	17	325	mk	2024-03-31	2.935269428	9	Invoice: 26RA-260091/2024, Supplier: KZ RADGONA Z.O.O.
19	4	18	200	mk	2024-03-31	2.7191962979999995	10	Invoice: 26RA-260090/2024, Supplier: KZ RADGONA Z.O.O.
20	4	19	200	mk	2024-03-31	2.622129692	10	Invoice: 26RA-260090/2024, Supplier: KZ RADGONA Z.O.O.
21	4	20	450	mk	2024-03-31	2.719196297999999	10	Invoice: 26RA-260090/2024, Supplier: KZ RADGONA Z.O.O.
22	4	21	6	L	2024-03-31	42.235619400000004	11	Invoice: 30RA-300318/2024, Supplier: KZ RADGONA Z.O.O.
23	4	22	375	mk	2024-03-31	2.8019689880000005	12	Invoice: 26RA-260086/2024, Supplier: KZ RADGONA Z.O.O.
24	4	23	400	mk	2024-03-31	2.884741496	12	Invoice: 26RA-260086/2024, Supplier: KZ RADGONA Z.O.O.
25	4	24	375	mk	2024-03-31	2.8847414960000006	12	Invoice: 26RA-260086/2024, Supplier: KZ RADGONA Z.O.O.
26	4	25	125	mk	2024-03-31	0.000364	12	Invoice: 26RA-260086/2024, Supplier: KZ RADGONA Z.O.O.
27	4	26	10	L	2024-03-31	66.05972652000001	13	Invoice: 26RA-260159/2024, Supplier: KZ RADGONA Z.O.O.
28	4	26	5	L	2024-05-31	64.12328796	14	Invoice: 26RA-260293/2024, Supplier: KZ RADGONA Z.O.O.
29	4	27	65	L	2024-05-31	49.99068431999999	14	Invoice: 26RA-260293/2024, Supplier: KZ RADGONA Z.O.O.
30	4	28	7	L	2024-05-31	61.23561750000001	14	Invoice: 26RA-260293/2024, Supplier: KZ RADGONA Z.O.O.
31	4	29	15	L	2024-05-31	22.048218659999996	15	Invoice: 54RA-540160/2024, Supplier: KZ RADGONA Z.O.O.
32	4	29	2	L	2024-05-31	25.054795199999997	15	Invoice: 54RA-540160/2024, Supplier: KZ RADGONA Z.O.O.
33	4	30	3	L	2024-05-31	72.99862949999999	15	Invoice: 54RA-540160/2024, Supplier: KZ RADGONA Z.O.O.
34	4	28	5	L	2024-05-31	57.57676686	15	Invoice: 54RA-540160/2024, Supplier: KZ RADGONA Z.O.O.
35	4	27	45	L	2024-05-31	49.99068432	16	Invoice: 29RA-290327/2024, Supplier: KZ RADGONA Z.O.O.
36	4	29	5	L	2024-05-31	24.205482000000003	16	Invoice: 29RA-290327/2024, Supplier: KZ RADGONA Z.O.O.
37	4	29	15	L	2024-05-31	22.523835539999997	16	Invoice: 29RA-290327/2024, Supplier: KZ RADGONA Z.O.O.
38	4	26	5	L	2024-05-31	63.684384	17	Invoice: 30RA-300583/2024, Supplier: KZ RADGONA Z.O.O.
39	4	31	24000	kg	2024-05-31	0.14200912999999998	18	Invoice: 26RA-260238/2024, Supplier: KZ RADGONA Z.O.O.
40	4	15	10500	kg	2024-05-31	0.30405479785714284	19	Invoice: 26RA-260244/2024, Supplier: KZ RADGONA Z.O.O.
41	4	26	40	L	2024-05-31	61.694247000000004	20	Invoice: 26RA-260158/2024, Supplier: KZ RADGONA Z.O.O.
42	4	26	1	L	2024-05-31	68.1150693	20	Invoice: 26RA-260158/2024, Supplier: KZ RADGONA Z.O.O.
43	4	32	4.5	L	2024-05-31	56.734240799999995	20	Invoice: 26RA-260158/2024, Supplier: KZ RADGONA Z.O.O.
44	4	33	1350	mk	2024-06-30	2.54467577	21	Invoice: 26RA-260306/24, Supplier: KZ RADGONA Z.O.O.
45	4	34	100	mk	2024-06-30	2.54467577	21	Invoice: 26RA-260306/24, Supplier: KZ RADGONA Z.O.O.
46	4	35	1100	mk	2024-06-30	2.586228372	21	Invoice: 26RA-260306/24, Supplier: KZ RADGONA Z.O.O.
47	4	36	250	mk	2024-06-30	0.3214612	21	Invoice: 26RA-260306/24, Supplier: KZ RADGONA Z.O.O.
48	4	37	9000	kg	2024-04-30	0.526065753	22	Invoice: 26RAÔÇÉ260156/2024, Supplier: KZ RADGONA Z.O.O.
49	4	38	10000	L	2024-04-13	0	\N	Farm-produced slurry
\.


--
-- Data for Name: inventory_deductions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY "public"."inventory_deductions" ("id", "task_id", "inventory_id", "quantity_used", "created_at") FROM stdin;
1	255	13	129.35	2025-05-20 22:28:57.686237
2	191	40	60.7	2025-05-20 22:28:57.686237
3	194	15	0.52	2025-05-20 22:28:57.686237
4	239	40	77.96	2025-05-20 22:28:57.686237
5	226	29	0.11	2025-05-20 22:28:57.686237
6	249	13	343.3	2025-05-20 22:28:57.686237
7	203	40	39.36	2025-05-20 22:28:57.686237
187	320	49	377463	2025-05-21 01:14:33.093025
9	167	40	385.36	2025-05-20 22:28:57.686237
10	207	13	345.38	2025-05-20 22:28:57.686237
11	177	13	158.15	2025-05-20 22:28:57.686237
12	159	13	2403.08	2025-05-20 22:28:57.686237
188	321	49	56253	2025-05-21 01:14:33.093025
189	322	49	122892	2025-05-21 01:14:33.093025
15	208	29	2.07	2025-05-20 22:28:57.686237
16	219	13	82.38	2025-05-20 22:28:57.686237
17	190	29	0.46	2025-05-20 22:28:57.686237
18	248	15	2.33	2025-05-20 22:28:57.686237
19	243	13	39.55	2025-05-20 22:28:57.686237
20	202	29	0.3	2025-05-20 22:28:57.686237
21	256	29	0.78	2025-05-20 22:28:57.686237
22	209	40	276.3	2025-05-20 22:28:57.686237
23	179	40	126.52	2025-05-20 22:28:57.686237
24	251	40	146.44	2025-05-20 22:28:57.686237
25	244	29	0.24	2025-05-20 22:28:57.686237
26	232	29	2.05	2025-05-20 22:28:57.686237
27	184	29	1.29	2025-05-20 22:28:57.686237
28	172	29	5.74	2025-05-20 22:28:57.686237
29	195	13	3763.43	2025-05-20 22:28:57.686237
30	218	15	0.56	2025-05-20 22:28:57.686237
31	154	29	0.74	2025-05-20 22:28:57.686237
32	185	40	224.28	2025-05-20 22:28:57.686237
33	197	40	3010.74	2025-05-20 22:28:57.686237
34	213	13	241.43	2025-05-20 22:28:57.686237
190	323	49	104559	2025-05-21 01:14:33.093025
36	166	29	2.89	2025-05-20 22:28:57.686237
37	155	40	1922.46	2025-05-20 22:28:57.686237
38	230	15	2.32	2025-05-20 22:28:57.686237
191	324	49	174297	2025-05-21 01:14:33.093025
41	254	15	1.24	2025-05-20 22:28:57.686237
42	176	15	1.08	2025-05-20 22:28:57.686237
43	238	29	0.58	2025-05-20 22:28:57.686237
44	196	29	22.58	2025-05-20 22:28:57.686237
45	161	40	2296.54	2025-05-20 22:28:57.686237
46	215	40	65.9	2025-05-20 22:28:57.686237
48	201	13	49.2	2025-05-20 22:28:57.686237
49	231	13	341.9	2025-05-20 22:28:57.686237
50	158	15	16.34	2025-05-20 22:28:57.686237
51	214	29	1.45	2025-05-20 22:28:57.686237
52	188	15	1.91	2025-05-20 22:28:57.686237
53	173	40	765.96	2025-05-20 22:28:57.686237
54	164	15	19.52	2025-05-20 22:28:57.686237
55	212	15	1.64	2025-05-20 22:28:57.686237
56	183	13	214.5	2025-05-20 22:28:57.686237
57	170	15	6.51	2025-05-20 22:28:57.686237
58	153	13	123.38	2025-05-20 22:28:57.686237
59	236	15	0.66	2025-05-20 22:28:57.686237
60	242	15	0.27	2025-05-20 22:28:57.686237
61	227	40	15.18	2025-05-20 22:28:57.686237
62	250	29	1.1	2025-05-20 22:28:57.686237
63	182	15	1.46	2025-05-20 22:28:57.686237
64	171	13	957.45	2025-05-20 22:28:57.686237
65	257	40	103.48	2025-05-20 22:28:57.686237
66	200	15	0.33	2025-05-20 22:28:57.686237
67	206	15	2.35	2025-05-20 22:28:57.686237
68	233	40	273.52	2025-05-20 22:28:57.686237
69	225	13	18.98	2025-05-20 22:28:57.686237
70	160	29	17.22	2025-05-20 22:28:57.686237
71	165	13	481.7	2025-05-20 22:28:57.686237
72	178	29	0.95	2025-05-20 22:28:57.686237
73	245	40	274.64	2025-05-20 22:28:57.686237
74	189	13	280.35	2025-05-20 22:28:57.686237
75	152	15	0.84	2025-05-20 22:28:57.686237
76	237	13	97.45	2025-05-20 22:28:57.686237
77	151	49	30000	2025-05-21 00:30:26.181214
78	253	49	30000	2025-05-21 00:30:26.181214
79	241	49	30000	2025-05-21 00:30:26.181214
80	193	49	30000	2025-05-21 00:30:26.181214
82	163	49	30000	2025-05-21 00:30:26.181214
83	211	49	30000	2025-05-21 00:30:26.181214
84	181	49	30000	2025-05-21 00:30:26.181214
85	175	49	30000	2025-05-21 00:30:26.181214
86	205	49	30000	2025-05-21 00:30:26.181214
87	187	49	30000	2025-05-21 00:30:26.181214
88	235	49	30000	2025-05-21 00:30:26.181214
89	247	49	30000	2025-05-21 00:30:26.181214
90	199	49	30000	2025-05-21 00:30:26.181214
91	229	49	30000	2025-05-21 00:30:26.181214
92	259	49	30000	2025-05-21 00:30:26.181214
93	169	49	30000	2025-05-21 00:30:26.181214
94	157	49	30000	2025-05-21 00:30:26.181214
96	217	49	30000	2025-05-21 00:30:26.181214
282	508	15	16.34	2025-05-21 01:55:00.277238
283	509	15	19.52	2025-05-21 01:55:00.277238
289	522	13	2403.07	2025-05-21 02:07:13.543948
290	523	13	2870.67	2025-05-21 02:07:13.543948
297	529	10	2.88369	2025-05-21 02:08:43.847306
298	529	11	9.6123	2025-05-21 02:08:43.847306
299	530	10	3.44481	2025-05-21 02:08:43.847306
300	530	11	11.4827	2025-05-21 02:08:43.847306
310	536	5	2883.69	2025-05-21 02:10:16.198655
275	501	49	30000	2025-05-21 01:53:27.241378
276	502	49	30000	2025-05-21 01:53:27.241378
311	537	5	3444.81	2025-05-21 02:10:16.198655
317	543	48	961.23	2025-05-21 02:11:03.197444
318	544	48	1148.27	2025-05-21 02:11:03.197444
324	550	40	961.23	2025-05-21 02:11:34.523067
325	551	40	1148.27	2025-05-21 02:11:34.523067
162	300	15	21.39	2025-05-21 01:09:54.907185
163	301	15	3.19	2025-05-21 01:09:54.907185
164	302	15	6.96	2025-05-21 01:09:54.907185
165	303	15	5.93	2025-05-21 01:09:54.907185
166	304	15	9.88	2025-05-21 01:09:54.907185
167	305	13	3145.53	2025-05-21 01:09:54.907185
168	306	13	468.78	2025-05-21 01:09:54.907185
169	307	13	1024.1	2025-05-21 01:09:54.907185
170	308	13	871.33	2025-05-21 01:09:54.907185
171	309	13	1452.48	2025-05-21 01:09:54.907185
172	310	29	18.87	2025-05-21 01:09:54.907185
173	311	29	2.81	2025-05-21 01:09:54.907185
174	312	29	6.14	2025-05-21 01:09:54.907185
175	313	29	5.23	2025-05-21 01:09:54.907185
176	314	29	8.71	2025-05-21 01:09:54.907185
177	315	40	2516.42	2025-05-21 01:09:54.907185
178	316	40	375.02	2025-05-21 01:09:54.907185
179	317	40	819.28	2025-05-21 01:09:54.907185
180	318	40	697.06	2025-05-21 01:09:54.907185
181	319	40	1161.98	2025-05-21 01:09:54.907185
\.


--
-- Data for Name: invoices; Type: TABLE DATA; Schema: public; Owner: -
--

COPY "public"."invoices" ("id", "farmer_id", "upload_date", "file_path", "extracted_data", "status", "needs_verification", "notes") FROM stdin;
1	\N	2023-10-20 00:00:00	\N	{"invoice_number": "26RA-260526/2023"}	\N	f	Supplier: KZ RADGONA Z.O.O.; Payment terms: 15.0
2	\N	2023-11-03 00:00:00	\N	{"invoice_number": "246558"}	\N	f	Supplier: RAIFFEISEN AGRO TRGOVINA D.O.O.; Payment terms: 237.0
3	\N	2024-02-21 00:00:00	\N	{"invoice_number": "223018"}	\N	f	Supplier: RAIFFEISEN AGRO TRGOVINA D.O.O.; Payment terms: 160.0
4	\N	2024-03-31 00:00:00	\N	{"invoice_number": "26RA-260144/2024"}	\N	f	Supplier: KZ RADGONA Z.O.O.; Payment terms: 15.0
5	\N	2024-03-31 00:00:00	\N	{"invoice_number": "26RA-26009872024"}	\N	f	Supplier: KZ RADGONA Z.O.O.; Payment terms: 15.0
6	\N	2024-03-31 00:00:00	\N	{"invoice_number": "26RA-260100/2024"}	\N	f	Supplier: KZ RADGONA Z.O.O.; Payment terms: 15.0
7	\N	2024-03-31 00:00:00	\N	{"invoice_number": "26RA-26009972024"}	\N	f	Supplier: KZ RADGONA Z.O.O.; Payment terms: 15.0
8	\N	2024-03-31 00:00:00	\N	{"invoice_number": "26RA-260097/2024"}	\N	f	Supplier: KZ RADGONA Z.O.O.; Payment terms: 15.0
9	\N	2024-03-31 00:00:00	\N	{"invoice_number": "26RA-260091/2024"}	\N	f	Supplier: KZ RADGONA Z.O.O.; Payment terms: 15.0
10	\N	2024-03-31 00:00:00	\N	{"invoice_number": "26RA-260090/2024"}	\N	f	Supplier: KZ RADGONA Z.O.O.; Payment terms: 15.0
11	\N	2024-03-31 00:00:00	\N	{"invoice_number": "30RA-300318/2024"}	\N	f	Supplier: KZ RADGONA Z.O.O.; Payment terms: 15.0
12	\N	2024-03-31 00:00:00	\N	{"invoice_number": "26RA-260086/2024"}	\N	f	Supplier: KZ RADGONA Z.O.O.; Payment terms: 15.0
13	\N	2024-03-31 00:00:00	\N	{"invoice_number": "26RA-260159/2024"}	\N	f	Supplier: KZ RADGONA Z.O.O.; Payment terms: 15.0
14	\N	2024-05-31 00:00:00	\N	{"invoice_number": "26RA-260293/2024"}	\N	f	Supplier: KZ RADGONA Z.O.O.; Payment terms: 15.0
15	\N	2024-05-31 00:00:00	\N	{"invoice_number": "54RA-540160/2024"}	\N	f	Supplier: KZ RADGONA Z.O.O.; Payment terms: 15.0
16	\N	2024-05-31 00:00:00	\N	{"invoice_number": "29RA-290327/2024"}	\N	f	Supplier: KZ RADGONA Z.O.O.; Payment terms: 15.0
17	\N	2024-05-31 00:00:00	\N	{"invoice_number": "30RA-300583/2024"}	\N	f	Supplier: KZ RADGONA Z.O.O.; Payment terms: 15.0
18	\N	2024-05-31 00:00:00	\N	{"invoice_number": "26RA-260238/2024"}	\N	f	Supplier: KZ RADGONA Z.O.O.; Payment terms: 15.0
19	\N	2024-05-31 00:00:00	\N	{"invoice_number": "26RA-260244/2024"}	\N	f	Supplier: KZ RADGONA Z.O.O.; Payment terms: 15.0
20	\N	2024-05-31 00:00:00	\N	{"invoice_number": "26RA-260158/2024"}	\N	f	Supplier: KZ RADGONA Z.O.O.; Payment terms: 15.0
21	\N	2024-06-30 00:00:00	\N	{"invoice_number": "26RA-260306/24"}	\N	f	Supplier: KZ RADGONA Z.O.O.; Payment terms: 165.0
22	\N	2024-04-30 00:00:00	\N	{"invoice_number": "26RAÔÇÉ260156/2024"}	\N	f	Supplier: KZ RADGONA Z.O.O.; Payment terms: 15.0
\.


--
-- Data for Name: material_catalog; Type: TABLE DATA; Schema: public; Owner: -
--

COPY "public"."material_catalog" ("id", "name", "brand", "group_name", "formulation", "unit", "notes") FROM stdin;
1	GEO	NO BRAND	wheat seed	\N	kg	\N
2	ELENA	AGROSAAT	barley seed	\N	kg	\N
3	IZALCO	AGROSAAT	wheat seed	\N	kg	\N
4	OBIWAN	AGROSAAT	wheat seed	\N	kg	\N
5	KAPPA 15-15-15	KAPPA	NPK fertilizer	\N	kg	\N
6	AXIAL ONE	SYNGENTA	herbicide	\N	L	\N
7	QUELEX	CORTEVA	herbicide	\N	kg	\N
8	MODDUS EVO	SYNGENTA	growth regulator	\N	L	\N
9	DELARO FORTE EC 280	BAYER	fungicide	\N	L	\N
10	HUSSAR STAR WG 20,66	BAYER	herbicide	\N	kg	\N
11	MERO EC 733	BAYER	adjuvant	\N	L	\N
12	PHOSAGRO UREA	PHOSAGRO	urea	\N	kg	\N
13	PH MINUS	KARSIA	spray adjuvant	\N	L	\N
14	N-LOCK SUPER	CORTEVA	fertilizer additive	\N	L	\N
15	GENEZIS KAN	GEMEZIS PETISO	CAN fertilizer	\N	kg	\N
16	P0710+ARTEMID+REDIGO	SAATBAU LINZ	maize seed	\N	mk	\N
17	P9398+ARTEMID+REDIGO	SAATBAU LINZ	maize seed	\N	mk	\N
18	ANTARO+FORCE	SAATBAU LINZ	maize seed	\N	mk	\N
19	ESTEVIO+FORCE	SAATBAU LINZ	maize seed	\N	mk	\N
20	ALENARO+FORCE+OP+INS	SAATBAU LINZ	maize seed	\N	mk	\N
21	AXIAL 50 EC	SYNGENTA	herbicide	\N	L	\N
22	LG 31.377 PRIME TREATMENT	LIMAGRAIN	maize seed	\N	mk	\N
23	LG 31.479 PRIME TREATMENT	LIMAGRAIN	maize seed	\N	mk	\N
24	LIMAGOLD PRIME	LIMAGRAIN	maize seed	\N	mk	\N
25	LG NONAME	LIMAGRAIN	maize seed	\N	mk	\N
26	ASCRA XPRO EC 260	BAYER	fungicide	\N	L	\N
27	MONSOON ACTIVE OD 56,5	BAYER	herbicide	\N	L	\N
28	PRAKTIS	SHARDA	fungicide	\N	L	\N
29	TEBUSHA	SHARDA	fungicide	\N	L	\N
30	DECIS 100 EC	BAYER	insecticide	\N	L	\N
31	PLON WAP	CALC GROUP	calcium fertilizer	\N	kg	\N
32	DELUKS	AGROPROAGRO	insecticide	\N	L	\N
33	FARADAY KORIT+FORCE	AGROMAG	maize seed	\N	mk	\N
34	HORNET FORCE	AGROMAG	maize seed	\N	mk	\N
35	METHOD FORCE	AGROMAG	maize seed	\N	mk	\N
36	AGROMAG NONAME	AGROMAG	maize seed	\N	mk	\N
37	N-GOOO 40N +2MgO+0,1Zn+5SO3	KAPPA	N fertilizer with inhibitor	\N	kg	\N
38	Slurry Bla┼ż Vrzel	\N	fertilizer	\N	L	Farm-specific slurry from Bla┼ż
39	N-LOC SUPER	\N	fertilizer additive	\N	L	N stabilizer
40	UREA	\N	urea	\N	kg	Standard nitrogen fertilizer (46%)
\.


--
-- Data for Name: orders; Type: TABLE DATA; Schema: public; Owner: -
--

COPY "public"."orders" ("id", "user_id", "total_amount", "order_date") FROM stdin;
\.


--
-- Data for Name: other_inputs; Type: TABLE DATA; Schema: public; Owner: -
--

COPY "public"."other_inputs" ("id", "product_name", "category", "description", "notes", "country") FROM stdin;
\.


--
-- Data for Name: pending_messages; Type: TABLE DATA; Schema: public; Owner: -
--

COPY "public"."pending_messages" ("id", "farmer_id", "phone_number", "message_text", "status", "requires_consultation", "created_at") FROM stdin;
26	1	+38641348050	Question: Was a soil analysis done on your fields? (Yes/No)	approved	f	2025-05-19 21:38:31.268231
27	1	+38641348050	Question: Was a soil analysis done on your vineyard? (Yes/No)	approved	f	2025-05-19 21:46:19.621113
5	3	+4915156006708	Question: Can you tell me your expected yield for this crop in tons per hectare?	approved	f	2025-05-18 19:48:44.648374
4	3	+4915156006708	Question: Can you tell me your expected yield for this crop in tons per hectare?	approved	f	2025-05-18 19:45:08.067459
2	3	+4915156006708	Question: Kannst du mir deine erwartete Ernte f├╝r diese Kultur in Tonnen pro Hektar mitteilen?	approved	f	2025-05-18 17:08:50.918723
3	1	+38641348050	Question: Was a soil analysis done on your fields? (Yes/No)	approved	f	2025-05-18 17:28:37.353419
1	3	+4915156006708	Question: Can you tell me your expected yield for this crop in tons per hectare?	approved	f	2025-05-18 17:02:40.40538
6	3	+4915156006708	Question: Can you tell me if a soil analysis was done on your fields? (Yes/No)	approved	f	2025-05-18 19:58:19.062552
7	3	+4915156006708	Question: Do you have any fertilizer in stock? (Yes/No)	approved	f	2025-05-18 20:01:18.987047
8	3	+4915156006708	Question: Was a soil analysis done on your fields? (Yes/No)	approved	f	2025-05-18 20:02:45.456518
9	1	+38641348050	Question: Was a soil analysis done on your fields? (Yes/No)	approved	f	2025-05-18 20:14:02.802943
10	1	+38641348050	Question: Do you have any fertilizer in stock? (Yes/No)	approved	f	2025-05-18 20:14:37.933525
11	1	+38641348050	Question: Do you have any fertilizer in stock? (Yes/No)	approved	f	2025-05-18 20:18:44.218319
12	1	+38641348050	Question: Do you have any fertilizer in stock? (Yes/No)	approved	f	2025-05-19 08:18:39.276046
15	1	+38641348050	Question: Do you have any fertilizer in stock? (Yes/No)	approved	f	2025-05-19 11:34:43.656521
14	1	+38641348050	Question: Do you have any fertilizer in stock? (Yes/No)	approved	f	2025-05-19 09:09:59.474358
23	1	+38641348050	Question: Do you have any fertilizer in stock? (Yes/No)	approved	f	2025-05-19 21:19:46.254645
22	1	+38641348050	Question: Can you tell me your expected yield for this crop in tons per hectare?	approved	f	2025-05-19 21:13:32.914875
21	1	+38641348050	Question: Can you tell me your expected yield for the "Je─Źmen/TDM/Lucerna" crop in tons per hectare?	approved	f	2025-05-19 21:13:08.850914
20	1	+38641348050	Question: Can you tell me your expected yield for the Je─Źmen/TDM/Lucerna crop in tons per hectare?	approved	f	2025-05-19 21:09:08.510577
19	1	+38641348050	Question: Can you tell me your expected yield for the crop in tons per hectare?	approved	f	2025-05-19 21:04:35.872604
18	1	+38641348050	Question: Can you tell me your expected yield for the "Je─Źmen/TDM/Lucerna" crop in tons per hectare?	approved	f	2025-05-19 21:04:11.362877
17	1	+38641348050	Question: Can you tell me your expected yield for the crop in tons per hectare?	approved	f	2025-05-19 21:02:35.465337
25	1	+38641348050	Question: Was a soil analysis done on your fields? (Yes/No)	approved	f	2025-05-19 21:36:22.312299
24	1	+38641348050	Question: Do you have any fertilizer in stock? (Yes/No)	approved	f	2025-05-19 21:35:54.955381
28	1	+38641348050	Question: Do you have any fertilizer in stock? (Yes/No)	approved	f	2025-05-19 21:51:16.636782
29	1	+38641348050	Question: Can you tell me your expected yield for the "Je─Źmen/TDM/Lucerna" crop in tons per hectare?	approved	f	2025-05-19 21:51:45.658552
30	1	+38641348050	Question: Can you provide the N:P:K ratio of the fertilizer you have in stock?	approved	f	2025-05-19 21:52:26.46033
31	1	+38641348050	Question: Can you tell me your expected yield for your vineyard in tons per hectare?	approved	f	2025-05-19 21:58:09.031975
32	1	+38641348050	Question: Was a soil analysis done on your vineyard? (Yes/No)	approved	f	2025-05-19 21:58:30.434751
33	1	+38641348050	Question: Can you tell me if you have any fertilizer in stock? (Yes/No)	approved	f	2025-05-19 21:58:52.491338
34	1	+38641348050	Question: Can you tell me your expected yield for your vineyard in tons per hectare?	approved	f	2025-05-19 21:59:36.661713
36	1	+38641348050	Question: Can you tell me your expected yield for your vineyard in tons per hectare?	approved	f	2025-05-19 22:03:15.303758
35	3	+4915156006708	Question: Was a soil analysis done on your fields? (Yes/No)	approved	f	2025-05-19 22:03:05.073578
37	1	+38641348050	Question: Can you confirm if a soil analysis was done on your vineyard? (Yes/No)	approved	f	2025-05-19 22:04:05.963756
38	3	+4915156006708	Question: Was a soil analysis done on your fields? (Yes/No)	approved	f	2025-05-19 22:05:33.495613
39	1	+38641348050	Question: Can you confirm if a soil analysis was done on your vineyard? (Yes/No)	approved	f	2025-05-19 22:06:22.179666
42	3	+4915156006708	Question: Can you tell me your expected yield for this crop in tons per hectare?	approved	f	2025-05-19 22:14:10.004553
40	3	+4915156006708	Question: Can you tell me your expected yield for this crop in tons per hectare?	approved	f	2025-05-19 22:13:40.091738
41	3	+4915156006708	Question: Can you tell me your expected yield for this crop in tons per hectare?	approved	f	2025-05-19 22:13:42.54676
45	1	+38641348050	Question: Can you tell me your expected yield for this crop in tons per hectare?	approved	f	2025-05-19 22:25:13.87769
43	3	+4915156006708	Question: Do you have any fertilizer in stock? (Yes/No)	approved	f	2025-05-19 22:17:48.239244
44	3	+4915156006708	Question: Can you tell me your expected yield for this crop in tons per hectare?	approved	f	2025-05-19 22:20:15.367853
16	3	+4915156006708	Question: Can you tell me if you have any specific fertilizer needs based on the crop you're growing?	rejected	f	2025-05-19 12:03:55.087449
13	3	+4915156006708	Question: Can you tell me if a soil analysis was done on your fields? (Yes/No)	rejected	f	2025-05-19 08:26:52.74102
46	1	+38641348050	Question: Can you tell me your expected yield for this crop in tons per hectare?	approved	f	2025-05-19 22:25:43.883649
47	1	+38641348050	Question: Can you tell me your expected yield for this crop in tons per hectare?	approved	f	2025-05-19 22:28:31.929459
48	1	+38641348050	Question: Was a soil analysis done on your fields? (Yes/No)	approved	f	2025-05-19 22:29:33.186882
49	1	+38641348050	Question: Can you tell me your expected yield for this crop in tons per hectare?	rejected	f	2025-05-19 22:30:50.008594
50	1	+38641348050	Question: Can you tell me your expected yield for this crop in tons per hectare?	approved	f	2025-05-19 22:33:38.055624
51	1	+38641348050	Question: Was a soil analysis done on your fields? (Yes/No)	approved	f	2025-05-19 22:34:15.724107
52	1	+38641348050	Question: Can you tell me your expected yield for this crop in tons per hectare?	rejected	f	2025-05-19 22:35:02.141779
53	1	+38641348050	Question: Can you tell me your expected yield for this crop in tons per hectare?	approved	f	2025-05-19 22:38:19.842139
54	1	+38641348050	Question: Can you tell me if a soil analysis was done on your fields? (Yes/No)	approved	f	2025-05-19 22:38:44.243452
55	1	+38641348050	Question: Can you tell me your expected yield for this crop in tons per hectare?	approved	f	2025-05-19 22:38:59.926772
\.


--
-- Data for Name: seeds; Type: TABLE DATA; Schema: public; Owner: -
--

COPY "public"."seeds" ("id", "name", "crop_type", "notes", "producer", "maturity_group", "purpose", "plant_density_from", "plant_density_to", "unit_for_sowing_rate", "country") FROM stdin;
\.


--
-- Data for Name: task_fields; Type: TABLE DATA; Schema: public; Owner: -
--

COPY "public"."task_fields" ("task_id", "field_id") FROM stdin;
145	5
146	5
147	5
148	5
500	6
501	7
502	8
503	9
504	10
505	11
506	12
507	6
508	7
509	8
510	9
511	10
512	11
513	12
514	6
515	7
516	8
517	9
518	10
519	11
520	12
521	6
522	7
523	8
524	9
525	10
526	11
527	12
528	6
529	7
530	8
531	9
532	10
533	11
534	12
535	6
536	7
537	8
538	9
539	10
540	11
541	12
542	6
543	7
544	8
545	9
546	10
547	11
548	12
549	6
550	7
551	8
552	9
553	10
554	11
555	12
556	6
557	7
558	8
559	9
560	10
561	11
562	12
149	5
150	6
151	6
152	6
153	6
154	6
155	7
156	7
157	7
158	7
159	7
160	8
161	8
162	8
163	8
164	8
165	9
166	9
167	9
168	9
169	9
170	10
171	10
172	10
173	10
174	10
175	11
176	11
177	11
178	11
179	11
180	12
181	12
182	12
183	12
184	12
185	13
186	13
187	13
188	13
189	13
190	14
191	14
192	14
193	14
194	14
195	15
196	15
197	15
198	15
199	15
200	16
201	16
202	16
203	16
204	16
205	17
206	17
207	17
208	17
209	17
210	18
211	18
212	18
213	18
214	18
215	19
216	19
217	19
218	19
219	19
220	20
221	20
222	20
223	20
224	20
225	21
226	21
227	21
228	21
229	21
230	22
231	22
232	22
233	22
234	22
235	23
236	23
237	23
238	23
239	23
240	24
241	24
242	24
243	24
244	24
245	25
246	25
247	25
248	25
249	25
250	26
251	26
252	26
253	26
254	26
255	27
256	27
257	27
258	27
259	27
276	5
276	6
284	1
284	2
284	3
284	4
284	5
285	1
285	2
285	3
285	4
285	5
286	1
286	2
286	3
286	4
286	5
287	1
287	2
287	3
287	4
287	5
288	1
288	2
288	3
288	4
288	5
289	1
289	2
289	3
289	4
289	5
290	1
290	2
290	3
290	4
290	5
284	20
284	29
284	34
284	35
284	39
285	20
285	29
285	34
285	35
285	39
286	20
286	29
286	34
286	35
286	39
287	20
287	29
287	34
287	35
287	39
288	20
288	29
288	34
288	35
288	39
289	20
289	29
289	34
289	35
289	39
290	20
290	29
290	34
290	35
290	39
300	20
301	29
302	34
303	35
276	11
304	39
305	20
306	29
307	34
308	35
309	39
310	20
311	29
312	34
313	35
314	39
315	20
316	29
317	34
318	35
319	39
320	20
321	29
322	34
323	35
324	39
276	12
276	13
276	14
276	16
276	17
276	18
276	19
276	22
276	28
276	30
276	32
276	36
276	37
276	38
276	40
276	41
276	42
276	47
276	33
\.


--
-- Data for Name: task_material_dose; Type: TABLE DATA; Schema: public; Owner: -
--

COPY "public"."task_material_dose" ("task_type", "material_id", "crop_name", "year", "farmer_id", "rate_per_ha", "rate_unit") FROM stdin;
manure spreading	38	Corn (grain)	2024	4	20000	L
fertilizer additive	15	Corn (grain)	2024	4	1.7	L
sowing	13	Corn (grain)	2024	4	250	kg
spraying	29	Corn (grain)	2024	4	1.5	L
cultivation of crops	40	Corn (grain)	2024	4	200	kg
\.


--
-- Data for Name: task_materials; Type: TABLE DATA; Schema: public; Owner: -
--

COPY "public"."task_materials" ("task_id", "inventory_id", "quantity") FROM stdin;
\.


--
-- Data for Name: task_types; Type: TABLE DATA; Schema: public; Owner: -
--

COPY "public"."task_types" ("id", "name", "description") FROM stdin;
1	sowing	Seed placement or drilling
2	harvest	Grain crop harvesting
3	silage harvest	Harvesting of silage crops like maize
4	basic fertilization (P, K)	Pre-sowing application of phosphorus and potassium
5	N-fertilization	Application of nitrogen fertilizers during growth
6	spraying	Application of crop protection products
7	weed control (mechanical)	Mechanical weed removal
8	tillage	Soil preparation including ploughing, disking
9	soil sampling	Soil testing for nutrient and pH analysis
10	growth check	Observation of crop development stages
11	lime application	Application of lime to adjust soil pH
12	manure spreading	Application of organic solid manure
13	irrigation	Water application to crops
14	cultivation of crops	Inter-row cultivation or weeding
\.


--
-- Data for Name: tasks; Type: TABLE DATA; Schema: public; Owner: -
--

COPY "public"."tasks" ("id", "task_type", "description", "quantity", "date_performed", "status", "inventory_id", "notes", "crop_name", "machinery_id", "rate_per_ha", "rate_unit") FROM stdin;
277	Subsoiling	Silage maize subsoiling	\N	2024-05-16	pending	\N	\N	\N	\N	\N	\N
278	manure spreading	Silage maize slurry	\N	2024-05-13	pending	\N	\N	\N	\N	\N	\N
282	Cultivation	KAN silage cultivation	\N	2024-06-25	pending	\N	\N	\N	\N	\N	\N
283	Harvest (silage)	Silage harvest	\N	2024-10-08	pending	\N	\N	\N	\N	\N	\N
284	Subsoiling	Silage maize subsoiling	\N	2024-05-16	pending	\N	\N	\N	\N	\N	\N
285	manure spreading	Silage maize slurry	\N	2024-05-13	pending	\N	\N	\N	\N	\N	\N
289	Cultivation	KAN silage cultivation	\N	2024-06-25	pending	\N	\N	\N	\N	\N	\N
290	Harvest (silage)	Silage harvest	\N	2024-10-08	pending	\N	\N	\N	\N	\N	\N
501	manure spreading	\N	\N	2023-10-08	pending	\N	\N	Wheat (grain, straw left)	\N	\N	\N
502	manure spreading	\N	\N	2023-10-08	pending	\N	\N	Wheat (grain, straw left)	\N	\N	\N
508	Fertilizer additive	\N	\N	2023-10-07	pending	\N	\N	Wheat (grain, straw left)	\N	\N	\N
509	Fertilizer additive	\N	\N	2023-10-07	pending	\N	\N	Wheat (grain, straw left)	\N	\N	\N
1	Spraying	Sprayed Mikal 3 kg/ha on North Field	3	2025-05-12	pending	\N	\N	\N	\N	\N	\N
2	Spraying	Sprayed Luna 2 L/ha on North Field	2	2025-05-12	pending	\N	\N	\N	\N	\N	\N
180	Harvest	\N	\N	2024-10-10	pending	\N	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
156	Harvest	\N	\N	2024-10-10	pending	\N	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
189	Sowing	\N	\N	2024-04-29	pending	13	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
3	Spraying	Popr┼íkal sem Actara 0,8 kg na Zapadnoj vinogradu danes.	0.8	2025-05-13	pending	\N	\N	\N	\N	\N	\N
4	Spraying	Popr┼íkal sem Actara 0,8 kg na Zapadnoj vinogradu danes.	0.8	2025-05-13	pending	\N	\N	\N	\N	\N	\N
5	Spraying	poprskala sam western vineyard mikalom 3 kg	3	2025-05-13	pending	\N	\N	\N	\N	\N	\N
171	Sowing	\N	\N	2024-04-29	pending	13	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
279	Fertilizer Additive	N-Lock silage	\N	2024-05-12	pending	\N	\N	\N	\N	\N	\N
280	Sowing	Silage maize sowing with urea	\N	2024-05-18	pending	\N	\N	\N	\N	\N	\N
281	Spraying	Monsoon Active silage	\N	2024-06-18	pending	\N	\N	\N	\N	\N	\N
286	Fertilizer Additive	N-Lock silage	\N	2024-05-12	pending	\N	\N	\N	\N	\N	\N
287	Sowing	Silage maize sowing with urea	\N	2024-05-18	pending	\N	\N	\N	\N	\N	\N
288	Spraying	Monsoon Active silage	\N	2024-06-18	pending	\N	\N	\N	\N	\N	\N
201	Sowing	\N	\N	2024-04-29	pending	13	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
195	Sowing	\N	\N	2024-04-29	pending	13	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
152	Fertilizer Additive	\N	\N	2024-04-12	pending	15	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
164	Fertilizer Additive	\N	\N	2024-04-12	pending	15	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
159	Sowing	\N	\N	2024-04-29	pending	13	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
186	Harvest	\N	\N	2024-10-10	pending	\N	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
177	Sowing	\N	\N	2024-04-29	pending	13	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
162	Harvest	\N	\N	2024-10-10	pending	\N	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
192	Harvest	\N	\N	2024-10-10	pending	\N	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
153	Sowing	\N	\N	2024-04-29	pending	13	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
147	Sowing	\N	\N	2024-04-29	pending	13	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
198	Harvest	\N	\N	2024-10-10	pending	\N	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
165	Sowing	\N	\N	2024-04-29	pending	13	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
174	Harvest	\N	\N	2024-10-10	pending	\N	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
168	Harvest	\N	\N	2024-10-10	pending	\N	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
515	Subsoiling	\N	\N	2023-10-09	pending	\N	\N	Wheat (grain, straw left)	\N	\N	\N
516	Subsoiling	\N	\N	2023-10-09	pending	\N	\N	Wheat (grain, straw left)	\N	\N	\N
158	Fertilizer Additive	\N	\N	2024-04-12	pending	15	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
207	Sowing	\N	\N	2024-04-29	pending	13	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
183	Sowing	\N	\N	2024-04-29	pending	13	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
150	Harvest	\N	\N	2024-10-10	pending	\N	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
240	Harvest	\N	\N	2024-10-10	pending	\N	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
217	manure spreading	\N	\N	2024-04-13	pending	49	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
229	manure spreading	\N	\N	2024-04-13	pending	49	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
210	Harvest	\N	\N	2024-10-10	pending	\N	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
160	Spraying	\N	\N	2024-05-19	pending	29	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
235	manure spreading	\N	\N	2024-04-13	pending	49	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
223	manure spreading	\N	\N	2024-04-13	pending	49	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
204	Harvest	\N	\N	2024-10-10	pending	\N	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
219	Sowing	\N	\N	2024-04-29	pending	13	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
252	Harvest	\N	\N	2024-10-10	pending	\N	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
231	Sowing	\N	\N	2024-04-29	pending	13	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
246	Harvest	\N	\N	2024-10-10	pending	\N	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
243	Sowing	\N	\N	2024-04-29	pending	13	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
166	Spraying	\N	\N	2024-05-19	pending	29	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
264	Harvest	\N	\N	2024-10-10	pending	\N	Task for Corn (grain) - Bla┼ż Vrzel	\N	\N	\N	\N
270	Harvest	\N	\N	2024-10-10	pending	\N	Task for Corn (grain) - Bla┼ż Vrzel	\N	\N	\N	\N
222	Harvest	\N	\N	2024-10-10	pending	\N	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
228	Harvest	\N	\N	2024-10-10	pending	\N	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
258	Harvest	\N	\N	2024-10-10	pending	\N	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
276	Harvest	\N	\N	2024-10-10	pending	\N	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
237	Sowing	\N	\N	2024-04-29	pending	13	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
249	Sowing	\N	\N	2024-04-29	pending	13	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
255	Sowing	\N	\N	2024-04-29	pending	13	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
225	Sowing	\N	\N	2024-04-29	pending	13	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
216	Harvest	\N	\N	2024-10-10	pending	\N	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
213	Sowing	\N	\N	2024-04-29	pending	13	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
261	Sowing	\N	\N	2024-04-29	pending	13	Task for Corn (grain) - Bla┼ż Vrzel	\N	\N	\N	\N
267	Sowing	\N	\N	2024-04-29	pending	13	Task for Corn (grain) - Bla┼ż Vrzel	\N	\N	\N	\N
211	manure spreading	\N	\N	2024-04-13	pending	49	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
273	Sowing	\N	\N	2024-04-29	pending	13	Task for Corn (grain) - Bla┼ż Vrzel	\N	\N	\N	\N
154	Spraying	\N	\N	2024-05-19	pending	29	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
234	Harvest	\N	\N	2024-10-10	pending	\N	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
148	Spraying	\N	\N	2024-05-19	pending	29	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
208	Spraying	\N	\N	2024-05-19	pending	29	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
191	Cultivation Of Crops	\N	\N	2024-05-25	pending	40	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
256	Spraying	\N	\N	2024-05-19	pending	29	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
522	Sowing	\N	\N	2023-10-11	pending	\N	\N	Wheat (grain, straw left)	\N	\N	\N
523	Sowing	\N	\N	2023-10-11	pending	\N	\N	Wheat (grain, straw left)	\N	\N	\N
529	Spraying	\N	\N	2024-03-15	pending	\N	\N	Wheat (grain, straw left)	\N	\N	\N
530	Spraying	\N	\N	2024-03-15	pending	\N	\N	Wheat (grain, straw left)	\N	\N	\N
262	Spraying	\N	\N	2024-05-19	pending	29	Task for Corn (grain) - Bla┼ż Vrzel	\N	\N	\N	\N
268	Spraying	\N	\N	2024-05-19	pending	29	Task for Corn (grain) - Bla┼ż Vrzel	\N	\N	\N	\N
274	Spraying	\N	\N	2024-05-19	pending	29	Task for Corn (grain) - Bla┼ż Vrzel	\N	\N	\N	\N
184	Spraying	\N	\N	2024-05-19	pending	29	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
190	Spraying	\N	\N	2024-05-19	pending	29	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
197	Cultivation Of Crops	\N	\N	2024-05-25	pending	40	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
227	Cultivation Of Crops	\N	\N	2024-05-25	pending	40	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
173	Cultivation Of Crops	\N	\N	2024-05-25	pending	40	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
149	Cultivation Of Crops	\N	\N	2024-05-25	pending	40	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
239	Cultivation Of Crops	\N	\N	2024-05-25	pending	40	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
161	Cultivation Of Crops	\N	\N	2024-05-25	pending	40	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
196	Spraying	\N	\N	2024-05-19	pending	29	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
226	Spraying	\N	\N	2024-05-19	pending	29	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
244	Spraying	\N	\N	2024-05-19	pending	29	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
179	Cultivation Of Crops	\N	\N	2024-05-25	pending	40	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
233	Cultivation Of Crops	\N	\N	2024-05-25	pending	40	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
220	Spraying	\N	\N	2024-05-19	pending	29	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
155	Cultivation Of Crops	\N	\N	2024-05-25	pending	40	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
250	Spraying	\N	\N	2024-05-19	pending	29	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
178	Spraying	\N	\N	2024-05-19	pending	29	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
203	Cultivation Of Crops	\N	\N	2024-05-25	pending	40	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
238	Spraying	\N	\N	2024-05-19	pending	29	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
214	Spraying	\N	\N	2024-05-19	pending	29	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
202	Spraying	\N	\N	2024-05-19	pending	29	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
232	Spraying	\N	\N	2024-05-19	pending	29	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
172	Spraying	\N	\N	2024-05-19	pending	29	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
209	Cultivation Of Crops	\N	\N	2024-05-25	pending	40	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
221	Cultivation Of Crops	\N	\N	2024-05-25	pending	40	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
167	Cultivation Of Crops	\N	\N	2024-05-25	pending	40	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
536	Fertilizing	\N	\N	2024-03-03	pending	\N	\N	Wheat (grain, straw left)	\N	\N	\N
537	Fertilizing	\N	\N	2024-03-03	pending	\N	\N	Wheat (grain, straw left)	\N	\N	\N
543	Fertilizing	\N	\N	2024-05-02	pending	\N	\N	Wheat (grain, straw left)	\N	\N	\N
544	Fertilizing	\N	\N	2024-05-02	pending	\N	\N	Wheat (grain, straw left)	\N	\N	\N
550	Fertilizing	\N	\N	2024-05-22	pending	\N	\N	Wheat (grain, straw left)	\N	\N	\N
551	Fertilizing	\N	\N	2024-05-22	pending	\N	\N	Wheat (grain, straw left)	\N	\N	\N
557	Harvest	\N	\N	2024-07-06	pending	\N	\N	Wheat (grain, straw left)	\N	\N	\N
558	Harvest	\N	\N	2024-07-06	pending	\N	\N	Wheat (grain, straw left)	\N	\N	\N
169	manure spreading	\N	\N	2024-04-13	pending	49	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
265	manure spreading	\N	\N	2024-04-13	pending	49	Task for Corn (grain) - Bla┼ż Vrzel	\N	\N	\N	\N
271	manure spreading	\N	\N	2024-04-13	pending	49	Task for Corn (grain) - Bla┼ż Vrzel	\N	\N	\N	\N
187	manure spreading	\N	\N	2024-04-13	pending	49	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
181	manure spreading	\N	\N	2024-04-13	pending	49	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
241	manure spreading	\N	\N	2024-04-13	pending	49	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
175	manure spreading	\N	\N	2024-04-13	pending	49	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
253	manure spreading	\N	\N	2024-04-13	pending	49	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
199	manure spreading	\N	\N	2024-04-13	pending	49	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
193	manure spreading	\N	\N	2024-04-13	pending	49	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
145	manure spreading	\N	\N	2024-04-13	pending	49	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
259	manure spreading	\N	\N	2024-04-13	pending	49	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
151	manure spreading	\N	\N	2024-04-13	pending	49	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
205	manure spreading	\N	\N	2024-04-13	pending	49	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
163	manure spreading	\N	\N	2024-04-13	pending	49	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
157	manure spreading	\N	\N	2024-04-13	pending	49	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
247	manure spreading	\N	\N	2024-04-13	pending	49	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
185	Cultivation Of Crops	\N	\N	2024-05-25	pending	40	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
215	Cultivation Of Crops	\N	\N	2024-05-25	pending	40	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
176	Fertilizer Additive	\N	\N	2024-04-12	pending	15	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
236	Fertilizer Additive	\N	\N	2024-04-12	pending	15	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
188	Fertilizer Additive	\N	\N	2024-04-12	pending	15	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
242	Fertilizer Additive	\N	\N	2024-04-12	pending	15	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
230	Fertilizer Additive	\N	\N	2024-04-12	pending	15	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
182	Fertilizer Additive	\N	\N	2024-04-12	pending	15	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
170	Fertilizer Additive	\N	\N	2024-04-12	pending	15	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
212	Fertilizer Additive	\N	\N	2024-04-12	pending	15	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
194	Fertilizer Additive	\N	\N	2024-04-12	pending	15	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
206	Fertilizer Additive	\N	\N	2024-04-12	pending	15	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
224	Fertilizer Additive	\N	\N	2024-04-12	pending	15	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
248	Fertilizer Additive	\N	\N	2024-04-12	pending	15	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
218	Fertilizer Additive	\N	\N	2024-04-12	pending	15	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
254	Fertilizer Additive	\N	\N	2024-04-12	pending	15	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
146	Fertilizer Additive	\N	\N	2024-04-12	pending	15	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
200	Fertilizer Additive	\N	\N	2024-04-12	pending	15	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
260	Fertilizer Additive	\N	\N	2024-04-12	pending	15	Task for Corn (grain) - Bla┼ż Vrzel	\N	\N	\N	\N
266	Fertilizer Additive	\N	\N	2024-04-12	pending	15	Task for Corn (grain) - Bla┼ż Vrzel	\N	\N	\N	\N
272	Fertilizer Additive	\N	\N	2024-04-12	pending	15	Task for Corn (grain) - Bla┼ż Vrzel	\N	\N	\N	\N
300	Fertilizer additive	N-LOCK on HRASTJE	\N	2024-05-12	pending	\N	\N	\N	\N	\N	\N
301	Fertilizer additive	N-LOCK on STRAMI─î 2	\N	2024-05-12	pending	\N	\N	\N	\N	\N	\N
302	Fertilizer additive	N-LOCK on KRI┼ŻANI─î - 1	\N	2024-05-12	pending	\N	\N	\N	\N	\N	\N
303	Fertilizer additive	N-LOCK on SADOVNJAK	\N	2024-05-12	pending	\N	\N	\N	\N	\N	\N
304	Fertilizer additive	N-LOCK on PA┼áNIK	\N	2024-05-12	pending	\N	\N	\N	\N	\N	\N
305	Sowing	Sowing + Urea on HRASTJE	\N	2024-05-18	pending	\N	\N	\N	\N	\N	\N
306	Sowing	Sowing + Urea on STRAMI─î 2	\N	2024-05-18	pending	\N	\N	\N	\N	\N	\N
307	Sowing	Sowing + Urea on KRI┼ŻANI─î - 1	\N	2024-05-18	pending	\N	\N	\N	\N	\N	\N
308	Sowing	Sowing + Urea on SADOVNJAK	\N	2024-05-18	pending	\N	\N	\N	\N	\N	\N
309	Sowing	Sowing + Urea on PA┼áNIK	\N	2024-05-18	pending	\N	\N	\N	\N	\N	\N
310	Spraying	Monsoon spraying HRASTJE	\N	2024-06-18	pending	\N	\N	\N	\N	\N	\N
311	Spraying	Monsoon spraying STRAMI─î 2	\N	2024-06-18	pending	\N	\N	\N	\N	\N	\N
312	Spraying	Monsoon spraying KRI┼ŻANI─î - 1	\N	2024-06-18	pending	\N	\N	\N	\N	\N	\N
313	Spraying	Monsoon spraying SADOVNJAK	\N	2024-06-18	pending	\N	\N	\N	\N	\N	\N
314	Spraying	Monsoon spraying PA┼áNIK	\N	2024-06-18	pending	\N	\N	\N	\N	\N	\N
315	Cultivation	KAN cultivation HRASTJE	\N	2024-06-25	pending	\N	\N	\N	\N	\N	\N
316	Cultivation	KAN cultivation STRAMI─î 2	\N	2024-06-25	pending	\N	\N	\N	\N	\N	\N
317	Cultivation	KAN cultivation KRI┼ŻANI─î - 1	\N	2024-06-25	pending	\N	\N	\N	\N	\N	\N
318	Cultivation	KAN cultivation SADOVNJAK	\N	2024-06-25	pending	\N	\N	\N	\N	\N	\N
319	Cultivation	KAN cultivation PA┼áNIK	\N	2024-06-25	pending	\N	\N	\N	\N	\N	\N
320	manure spreading	Slurry spreading HRASTJE	\N	2024-05-13	pending	\N	\N	\N	\N	\N	\N
321	manure spreading	Slurry spreading STRAMI─î 2	\N	2024-05-13	pending	\N	\N	\N	\N	\N	\N
322	manure spreading	Slurry spreading KRI┼ŻANI─î - 1	\N	2024-05-13	pending	\N	\N	\N	\N	\N	\N
323	manure spreading	Slurry spreading SADOVNJAK	\N	2024-05-13	pending	\N	\N	\N	\N	\N	\N
324	manure spreading	Slurry spreading PA┼áNIK	\N	2024-05-13	pending	\N	\N	\N	\N	\N	\N
257	Cultivation Of Crops	\N	\N	2024-05-25	pending	40	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
251	Cultivation Of Crops	\N	\N	2024-05-25	pending	40	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
245	Cultivation Of Crops	\N	\N	2024-05-25	pending	40	Task for Corn (grain) - Bla┼ż Vrzel	Corn (grain)	\N	\N	\N
263	Cultivation Of Crops	\N	\N	2024-05-25	pending	40	Task for Corn (grain) - Bla┼ż Vrzel	\N	\N	\N	\N
269	Cultivation Of Crops	\N	\N	2024-05-25	pending	40	Task for Corn (grain) - Bla┼ż Vrzel	\N	\N	\N	\N
275	Cultivation Of Crops	\N	\N	2024-05-25	pending	40	Task for Corn (grain) - Bla┼ż Vrzel	\N	\N	\N	\N
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: -
--

COPY "public"."users" ("id", "username", "email", "created_at") FROM stdin;
\.


--
-- Data for Name: variety_trial_data; Type: TABLE DATA; Schema: public; Owner: -
--

COPY "public"."variety_trial_data" ("id", "name", "crop_type", "producer", "maturity_group", "purpose", "plant_density_from", "plant_density_to", "unit_for_sowing_rate", "location", "sowing_date", "harvest_date", "plants_per_ha", "moisture_at_harvest", "yield_kg_ha", "soil_type", "weather_conditions", "fertilization_used", "pest_resistance", "disease_incidence", "notes") FROM stdin;
\.


--
-- Data for Name: weather_data; Type: TABLE DATA; Schema: public; Owner: -
--

COPY "public"."weather_data" ("id", "field_id", "fetch_date", "latitude", "longitude", "current_temp_c", "current_soil_temp_10cm_c", "current_precip_mm", "current_humidity", "forecast") FROM stdin;
1	1	2025-05-14 20:56:40.11466	45.8145	15.9667	18.2	16.2	0	45	[{"date": "2025-05-14", "humidity": 56, "precip_mm": 0.0, "max_temp_c": 21.6, "min_temp_c": 7.6}, {"date": "2025-05-15", "humidity": 71, "precip_mm": 7.24, "max_temp_c": 22.9, "min_temp_c": 8.0}, {"date": "2025-05-16", "humidity": 67, "precip_mm": 0.0, "max_temp_c": 15.7, "min_temp_c": 7.4}, {"date": "2025-05-17", "humidity": 69, "precip_mm": 6.93, "max_temp_c": 18.9, "min_temp_c": 5.9}, {"date": "2025-05-18", "humidity": 85, "precip_mm": 4.84, "max_temp_c": 18.6, "min_temp_c": 7.2}, {"date": "2025-05-19", "humidity": 79, "precip_mm": 0.01, "max_temp_c": 20.0, "min_temp_c": 10.6}, {"date": "2025-05-20", "humidity": 67, "precip_mm": 0.0, "max_temp_c": 21.7, "min_temp_c": 10.2}]
2	2	2025-05-14 20:56:40.31078	45.815	15.967	18.2	16.2	0	45	[{"date": "2025-05-14", "humidity": 56, "precip_mm": 0.0, "max_temp_c": 21.6, "min_temp_c": 7.6}, {"date": "2025-05-15", "humidity": 71, "precip_mm": 7.24, "max_temp_c": 22.9, "min_temp_c": 8.0}, {"date": "2025-05-16", "humidity": 67, "precip_mm": 0.0, "max_temp_c": 15.7, "min_temp_c": 7.4}, {"date": "2025-05-17", "humidity": 69, "precip_mm": 6.93, "max_temp_c": 18.9, "min_temp_c": 5.9}, {"date": "2025-05-18", "humidity": 85, "precip_mm": 4.84, "max_temp_c": 18.6, "min_temp_c": 7.2}, {"date": "2025-05-19", "humidity": 79, "precip_mm": 0.01, "max_temp_c": 20.0, "min_temp_c": 10.6}, {"date": "2025-05-20", "humidity": 67, "precip_mm": 0.0, "max_temp_c": 21.7, "min_temp_c": 10.2}]
3	3	2025-05-14 20:56:40.512797	45.8155	15.9675	18.2	16.2	0	45	[{"date": "2025-05-14", "humidity": 56, "precip_mm": 0.0, "max_temp_c": 21.6, "min_temp_c": 7.6}, {"date": "2025-05-15", "humidity": 71, "precip_mm": 7.24, "max_temp_c": 22.9, "min_temp_c": 8.0}, {"date": "2025-05-16", "humidity": 67, "precip_mm": 0.0, "max_temp_c": 15.7, "min_temp_c": 7.4}, {"date": "2025-05-17", "humidity": 69, "precip_mm": 6.93, "max_temp_c": 18.9, "min_temp_c": 5.9}, {"date": "2025-05-18", "humidity": 85, "precip_mm": 4.84, "max_temp_c": 18.6, "min_temp_c": 7.2}, {"date": "2025-05-19", "humidity": 79, "precip_mm": 0.01, "max_temp_c": 20.0, "min_temp_c": 10.6}, {"date": "2025-05-20", "humidity": 67, "precip_mm": 0.0, "max_temp_c": 21.7, "min_temp_c": 10.2}]
\.


--
-- Name: advice_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('"public"."advice_log_id_seq"', 7, true);


--
-- Name: consultation_triggers_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('"public"."consultation_triggers_id_seq"', 1, false);


--
-- Name: cp_products_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('"public"."cp_products_id_seq"', 1, false);


--
-- Name: crop_nutrient_needs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('"public"."crop_nutrient_needs_id_seq"', 85, true);


--
-- Name: crop_protection_croatia_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('"public"."crop_protection_croatia_id_seq"', 1, false);


--
-- Name: crop_technology_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('"public"."crop_technology_id_seq"', 60, true);


--
-- Name: farm_machinery_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('"public"."farm_machinery_id_seq"', 1, false);


--
-- Name: farm_organic_fertilizers_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('"public"."farm_organic_fertilizers_id_seq"', 1, false);


--
-- Name: farmers_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('"public"."farmers_id_seq"', 4, true);


--
-- Name: fertilizers_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('"public"."fertilizers_id_seq"', 10, true);


--
-- Name: fields_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('"public"."fields_id_seq"', 53, true);


--
-- Name: growth_stage_reports_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('"public"."growth_stage_reports_id_seq"', 1, true);


--
-- Name: incoming_messages_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('"public"."incoming_messages_id_seq"', 359, true);


--
-- Name: inventory_deductions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('"public"."inventory_deductions_id_seq"', 329, true);


--
-- Name: inventory_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('"public"."inventory_id_seq"', 49, true);


--
-- Name: invoices_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('"public"."invoices_id_seq"', 22, true);


--
-- Name: material_catalog_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('"public"."material_catalog_id_seq"', 41, true);


--
-- Name: orders_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('"public"."orders_id_seq"', 1, false);


--
-- Name: other_inputs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('"public"."other_inputs_id_seq"', 1, false);


--
-- Name: pending_messages_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('"public"."pending_messages_id_seq"', 55, true);


--
-- Name: seeds_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('"public"."seeds_id_seq"', 1, false);


--
-- Name: task_types_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('"public"."task_types_id_seq"', 14, true);


--
-- Name: tasks_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('"public"."tasks_id_seq"', 290, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('"public"."users_id_seq"', 1, false);


--
-- Name: variety_trial_data_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('"public"."variety_trial_data_id_seq"', 1, false);


--
-- Name: weather_data_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('"public"."weather_data_id_seq"', 3, true);


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

