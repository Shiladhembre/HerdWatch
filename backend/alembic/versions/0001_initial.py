"""Initial PostgreSQL/PostGIS schema. Frozen; independent of future ORM changes."""

from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.execute(
        "\nCREATE TABLE historical_observations (\n\tsource_key VARCHAR(64) NOT NULL, \n\tsource VARCHAR(50) NOT NULL, \n\tdisease VARCHAR(150) NOT NULL, \n\tdistrict VARCHAR(150) NOT NULL, \n\traw_record JSONB NOT NULL, \n\tprovenance TEXT NOT NULL, \n\tid UUID NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tupdated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tCONSTRAINT pk_historical_observations PRIMARY KEY (id), \n\tCONSTRAINT uq_historical_observations_source_key UNIQUE (source_key)\n)\n\n"
    )
    op.execute("CREATE INDEX ix_historical_observations_created_at ON historical_observations (created_at)")
    op.execute("CREATE INDEX ix_historical_observations_disease ON historical_observations (disease)")
    op.execute("CREATE INDEX ix_historical_observations_district ON historical_observations (district)")
    op.execute("CREATE INDEX ix_historical_observations_source ON historical_observations (source)")
    op.execute(
        "\nCREATE TABLE locations (\n\tsource_key VARCHAR(100) NOT NULL, \n\tstate VARCHAR(100) NOT NULL, \n\tdistrict VARCHAR(100) NOT NULL, \n\tblock VARCHAR(100) NOT NULL, \n\tvillage VARCHAR(150) NOT NULL, \n\tstate_normalized VARCHAR(100) NOT NULL, \n\tdistrict_normalized VARCHAR(100) NOT NULL, \n\tblock_normalized VARCHAR(100) NOT NULL, \n\tvillage_normalized VARCHAR(150) NOT NULL, \n\tcattle_population INTEGER NOT NULL, \n\tbuffalo_population INTEGER NOT NULL, \n\tsheep_population INTEGER NOT NULL, \n\tgoat_population INTEGER NOT NULL, \n\tpig_population INTEGER NOT NULL, \n\tpoultry_population INTEGER NOT NULL, \n\ttotal_livestock INTEGER NOT NULL, \n\tid UUID NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tupdated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tCONSTRAINT pk_locations PRIMARY KEY (id), \n\tCONSTRAINT uq_locations_source_key UNIQUE (source_key)\n)\n\n"
    )
    op.execute("CREATE INDEX ix_locations_block_normalized ON locations (block_normalized)")
    op.execute("CREATE INDEX ix_locations_created_at ON locations (created_at)")
    op.execute("CREATE INDEX ix_locations_district_normalized ON locations (district_normalized)")
    op.execute("CREATE INDEX ix_locations_state_normalized ON locations (state_normalized)")
    op.execute("CREATE INDEX ix_locations_village_normalized ON locations (village_normalized)")
    op.execute(
        "\nCREATE TABLE users (\n\tfull_name VARCHAR(150) NOT NULL, \n\temail VARCHAR(254) NOT NULL, \n\tmobile VARCHAR(20) NOT NULL, \n\tpassword_hash VARCHAR(255) NOT NULL, \n\trole VARCHAR(30) NOT NULL, \n\tstate VARCHAR(100) NOT NULL, \n\tdistrict VARCHAR(100) NOT NULL, \n\tblock VARCHAR(100) NOT NULL, \n\tvillage VARCHAR(150) NOT NULL, \n\tis_active BOOLEAN NOT NULL, \n\tis_verified BOOLEAN NOT NULL, \n\tpreferred_language VARCHAR(5) NOT NULL, \n\tid UUID NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tupdated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tCONSTRAINT pk_users PRIMARY KEY (id), \n\tCONSTRAINT uq_users_email UNIQUE (email), \n\tCONSTRAINT uq_users_mobile UNIQUE (mobile)\n)\n\n"
    )
    op.execute("CREATE INDEX ix_users_created_at ON users (created_at)")
    op.execute("CREATE INDEX ix_users_district ON users (district)")
    op.execute("CREATE INDEX ix_users_role ON users (role)")
    op.execute(
        "\nCREATE TABLE animals (\n\towner_id UUID NOT NULL, \n\tanimal_tag VARCHAR(80) NOT NULL, \n\tspecies VARCHAR(30) NOT NULL, \n\tbreed VARCHAR(100) NOT NULL, \n\tsex VARCHAR(20) NOT NULL, \n\tdate_of_birth DATE, \n\tapproximate_age FLOAT, \n\tpregnancy_status VARCHAR(40) NOT NULL, \n\thealth_status VARCHAR(50) NOT NULL, \n\tid UUID NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tupdated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tstate VARCHAR(100) NOT NULL, \n\tdistrict VARCHAR(100) NOT NULL, \n\tblock VARCHAR(100) NOT NULL, \n\tvillage VARCHAR(150) NOT NULL, \n\tlatitude FLOAT, \n\tlongitude FLOAT, \n\tgeom geometry(POINT,4326), \n\tcreated_by UUID, \n\tupdated_by UUID, \n\tCONSTRAINT pk_animals PRIMARY KEY (id), \n\tCONSTRAINT ck_animals_positive_age CHECK (approximate_age >= 0), \n\tCONSTRAINT fk_animals_owner_id_users FOREIGN KEY(owner_id) REFERENCES users (id), \n\tCONSTRAINT uq_animals_animal_tag UNIQUE (animal_tag), \n\tCONSTRAINT fk_animals_created_by_users FOREIGN KEY(created_by) REFERENCES users (id), \n\tCONSTRAINT fk_animals_updated_by_users FOREIGN KEY(updated_by) REFERENCES users (id)\n)\n\n"
    )
    op.execute("CREATE INDEX idx_animals_geom ON animals USING gist (geom)")
    op.execute("CREATE INDEX ix_animals_block ON animals (block)")
    op.execute("CREATE INDEX ix_animals_created_at ON animals (created_at)")
    op.execute("CREATE INDEX ix_animals_district ON animals (district)")
    op.execute("CREATE INDEX ix_animals_health_status ON animals (health_status)")
    op.execute("CREATE INDEX ix_animals_owner_id ON animals (owner_id)")
    op.execute("CREATE INDEX ix_animals_species ON animals (species)")
    op.execute("CREATE INDEX ix_animals_village ON animals (village)")
    op.execute(
        "\nCREATE TABLE audit_logs (\n\tuser_id UUID, \n\taction VARCHAR(100) NOT NULL, \n\tentity_type VARCHAR(60) NOT NULL, \n\tentity_id UUID NOT NULL, \n\tmetadata JSONB NOT NULL, \n\tid UUID NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tupdated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tCONSTRAINT pk_audit_logs PRIMARY KEY (id), \n\tCONSTRAINT fk_audit_logs_user_id_users FOREIGN KEY(user_id) REFERENCES users (id)\n)\n\n"
    )
    op.execute("CREATE INDEX ix_audit_logs_created_at ON audit_logs (created_at)")
    op.execute("CREATE INDEX ix_audit_logs_entity_id ON audit_logs (entity_id)")
    op.execute("CREATE INDEX ix_audit_logs_entity_type ON audit_logs (entity_type)")
    op.execute("CREATE INDEX ix_audit_logs_user_id ON audit_logs (user_id)")
    op.execute(
        "\nCREATE TABLE auth_sessions (\n\tuser_id UUID NOT NULL, \n\trefresh_jti VARCHAR(36) NOT NULL, \n\texpires_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\trevoked BOOLEAN NOT NULL, \n\tid UUID NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tupdated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tCONSTRAINT pk_auth_sessions PRIMARY KEY (id), \n\tCONSTRAINT fk_auth_sessions_user_id_users FOREIGN KEY(user_id) REFERENCES users (id), \n\tCONSTRAINT uq_auth_sessions_refresh_jti UNIQUE (refresh_jti)\n)\n\n"
    )
    op.execute("CREATE INDEX ix_auth_sessions_created_at ON auth_sessions (created_at)")
    op.execute("CREATE INDEX ix_auth_sessions_user_id ON auth_sessions (user_id)")
    op.execute(
        "\nCREATE TABLE herds (\n\towner_id UUID NOT NULL, \n\therd_name VARCHAR(150) NOT NULL, \n\tspecies VARCHAR(30) NOT NULL, \n\tanimal_count INTEGER NOT NULL, \n\tid UUID NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tupdated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tstate VARCHAR(100) NOT NULL, \n\tdistrict VARCHAR(100) NOT NULL, \n\tblock VARCHAR(100) NOT NULL, \n\tvillage VARCHAR(150) NOT NULL, \n\tlatitude FLOAT, \n\tlongitude FLOAT, \n\tgeom geometry(POINT,4326), \n\tcreated_by UUID, \n\tupdated_by UUID, \n\tCONSTRAINT pk_herds PRIMARY KEY (id), \n\tCONSTRAINT ck_herds_positive_count CHECK (animal_count > 0), \n\tCONSTRAINT fk_herds_owner_id_users FOREIGN KEY(owner_id) REFERENCES users (id), \n\tCONSTRAINT fk_herds_created_by_users FOREIGN KEY(created_by) REFERENCES users (id), \n\tCONSTRAINT fk_herds_updated_by_users FOREIGN KEY(updated_by) REFERENCES users (id)\n)\n\n"
    )
    op.execute("CREATE INDEX idx_herds_geom ON herds USING gist (geom)")
    op.execute("CREATE INDEX ix_herds_block ON herds (block)")
    op.execute("CREATE INDEX ix_herds_created_at ON herds (created_at)")
    op.execute("CREATE INDEX ix_herds_district ON herds (district)")
    op.execute("CREATE INDEX ix_herds_owner_id ON herds (owner_id)")
    op.execute("CREATE INDEX ix_herds_species ON herds (species)")
    op.execute("CREATE INDEX ix_herds_village ON herds (village)")
    op.execute(
        "\nCREATE TABLE outbreaks (\n\ttitle VARCHAR(200) NOT NULL, \n\tsuspected_disease VARCHAR(150) NOT NULL, \n\tspecies VARCHAR(30) NOT NULL, \n\tstatus VARCHAR(30) NOT NULL, \n\trisk_level VARCHAR(10) NOT NULL, \n\tstarted_on DATE NOT NULL, \n\tconfirmed_on DATE, \n\tconfirmed_by UUID, \n\tevidence TEXT, \n\tid UUID NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tupdated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tstate VARCHAR(100) NOT NULL, \n\tdistrict VARCHAR(100) NOT NULL, \n\tblock VARCHAR(100) NOT NULL, \n\tvillage VARCHAR(150) NOT NULL, \n\tlatitude FLOAT, \n\tlongitude FLOAT, \n\tgeom geometry(POINT,4326), \n\tcreated_by UUID, \n\tupdated_by UUID, \n\tCONSTRAINT pk_outbreaks PRIMARY KEY (id), \n\tCONSTRAINT fk_outbreaks_confirmed_by_users FOREIGN KEY(confirmed_by) REFERENCES users (id), \n\tCONSTRAINT fk_outbreaks_created_by_users FOREIGN KEY(created_by) REFERENCES users (id), \n\tCONSTRAINT fk_outbreaks_updated_by_users FOREIGN KEY(updated_by) REFERENCES users (id)\n)\n\n"
    )
    op.execute("CREATE INDEX idx_outbreaks_geom ON outbreaks USING gist (geom)")
    op.execute("CREATE INDEX ix_outbreaks_block ON outbreaks (block)")
    op.execute("CREATE INDEX ix_outbreaks_created_at ON outbreaks (created_at)")
    op.execute("CREATE INDEX ix_outbreaks_district ON outbreaks (district)")
    op.execute("CREATE INDEX ix_outbreaks_status ON outbreaks (status)")
    op.execute("CREATE INDEX ix_outbreaks_suspected_disease ON outbreaks (suspected_disease)")
    op.execute("CREATE INDEX ix_outbreaks_village ON outbreaks (village)")
    op.execute(
        "\nCREATE TABLE animal_records (\n\tanimal_id UUID NOT NULL, \n\trecorded_by UUID NOT NULL, \n\trecord_type VARCHAR(50) NOT NULL, \n\trecorded_on DATE NOT NULL, \n\tnotes VARCHAR(5000) NOT NULL, \n\tid UUID NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tupdated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tCONSTRAINT pk_animal_records PRIMARY KEY (id), \n\tCONSTRAINT fk_animal_records_animal_id_animals FOREIGN KEY(animal_id) REFERENCES animals (id), \n\tCONSTRAINT fk_animal_records_recorded_by_users FOREIGN KEY(recorded_by) REFERENCES users (id)\n)\n\n"
    )
    op.execute("CREATE INDEX ix_animal_records_animal_id ON animal_records (animal_id)")
    op.execute("CREATE INDEX ix_animal_records_created_at ON animal_records (created_at)")
    op.execute(
        "\nCREATE TABLE cases (\n\tcase_reference VARCHAR(40) NOT NULL, \n\treporter_id UUID NOT NULL, \n\towner_id UUID NOT NULL, \n\tanimal_id UUID, \n\therd_id UUID, \n\tspecies VARCHAR(30) NOT NULL, \n\tsymptom_started_on DATE NOT NULL, \n\taffected_count INTEGER NOT NULL, \n\tdeath_count INTEGER NOT NULL, \n\tobserved_symptoms TEXT NOT NULL, \n\tseverity VARCHAR(20) NOT NULL, \n\tnotes TEXT NOT NULL, \n\tstatus VARCHAR(30) NOT NULL, \n\tassigned_veterinarian_id UUID, \n\tescalated BOOLEAN NOT NULL, \n\trisk_level VARCHAR(10) NOT NULL, \n\tsuspected_disease VARCHAR(150), \n\tclinical_assessment TEXT, \n\tclient_record_id VARCHAR(100), \n\trequest_hash VARCHAR(64), \n\tcreated_offline_at TIMESTAMP WITH TIME ZONE, \n\tid UUID NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tupdated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tstate VARCHAR(100) NOT NULL, \n\tdistrict VARCHAR(100) NOT NULL, \n\tblock VARCHAR(100) NOT NULL, \n\tvillage VARCHAR(150) NOT NULL, \n\tlatitude FLOAT, \n\tlongitude FLOAT, \n\tgeom geometry(POINT,4326), \n\tcreated_by UUID, \n\tupdated_by UUID, \n\tCONSTRAINT pk_cases PRIMARY KEY (id), \n\tCONSTRAINT ck_cases_one_subject CHECK ((animal_id IS NULL) <> (herd_id IS NULL)), \n\tCONSTRAINT ck_cases_valid_counts CHECK (affected_count > 0 AND death_count >= 0 AND death_count <= affected_count), \n\tCONSTRAINT uq_cases_reporter_id UNIQUE (reporter_id, client_record_id), \n\tCONSTRAINT uq_cases_case_reference UNIQUE (case_reference), \n\tCONSTRAINT fk_cases_reporter_id_users FOREIGN KEY(reporter_id) REFERENCES users (id), \n\tCONSTRAINT fk_cases_owner_id_users FOREIGN KEY(owner_id) REFERENCES users (id), \n\tCONSTRAINT fk_cases_animal_id_animals FOREIGN KEY(animal_id) REFERENCES animals (id), \n\tCONSTRAINT fk_cases_herd_id_herds FOREIGN KEY(herd_id) REFERENCES herds (id), \n\tCONSTRAINT fk_cases_assigned_veterinarian_id_users FOREIGN KEY(assigned_veterinarian_id) REFERENCES users (id), \n\tCONSTRAINT fk_cases_created_by_users FOREIGN KEY(created_by) REFERENCES users (id), \n\tCONSTRAINT fk_cases_updated_by_users FOREIGN KEY(updated_by) REFERENCES users (id)\n)\n\n"
    )
    op.execute("CREATE INDEX idx_cases_geom ON cases USING gist (geom)")
    op.execute("CREATE INDEX ix_cases_animal_id ON cases (animal_id)")
    op.execute("CREATE INDEX ix_cases_assigned_veterinarian_id ON cases (assigned_veterinarian_id)")
    op.execute("CREATE INDEX ix_cases_block ON cases (block)")
    op.execute("CREATE INDEX ix_cases_created_at ON cases (created_at)")
    op.execute("CREATE INDEX ix_cases_district ON cases (district)")
    op.execute("CREATE INDEX ix_cases_herd_id ON cases (herd_id)")
    op.execute("CREATE INDEX ix_cases_owner_id ON cases (owner_id)")
    op.execute("CREATE INDEX ix_cases_reporter_id ON cases (reporter_id)")
    op.execute("CREATE INDEX ix_cases_risk_level ON cases (risk_level)")
    op.execute("CREATE INDEX ix_cases_species ON cases (species)")
    op.execute("CREATE INDEX ix_cases_status ON cases (status)")
    op.execute("CREATE INDEX ix_cases_suspected_disease ON cases (suspected_disease)")
    op.execute("CREATE INDEX ix_cases_village ON cases (village)")
    op.execute(
        "\nCREATE TABLE vaccinations (\n\tanimal_id UUID, \n\therd_id UUID, \n\towner_id UUID NOT NULL, \n\tdistrict VARCHAR(100) NOT NULL, \n\tvillage VARCHAR(150) NOT NULL, \n\tvaccine_name VARCHAR(150) NOT NULL, \n\tdisease_target VARCHAR(150) NOT NULL, \n\tdose_number INTEGER NOT NULL, \n\tadministered_on DATE NOT NULL, \n\tnext_due_on DATE, \n\tadministered_by UUID NOT NULL, \n\tbatch_number VARCHAR(100), \n\tnotes TEXT NOT NULL, \n\tid UUID NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tupdated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tcreated_by UUID, \n\tupdated_by UUID, \n\tCONSTRAINT pk_vaccinations PRIMARY KEY (id), \n\tCONSTRAINT ck_vaccinations_one_subject CHECK ((animal_id IS NULL) <> (herd_id IS NULL)), \n\tCONSTRAINT ck_vaccinations_positive_dose CHECK (dose_number > 0), \n\tCONSTRAINT ck_vaccinations_ordered_dates CHECK (next_due_on IS NULL OR next_due_on >= administered_on), \n\tCONSTRAINT fk_vaccinations_animal_id_animals FOREIGN KEY(animal_id) REFERENCES animals (id), \n\tCONSTRAINT fk_vaccinations_herd_id_herds FOREIGN KEY(herd_id) REFERENCES herds (id), \n\tCONSTRAINT fk_vaccinations_owner_id_users FOREIGN KEY(owner_id) REFERENCES users (id), \n\tCONSTRAINT fk_vaccinations_administered_by_users FOREIGN KEY(administered_by) REFERENCES users (id), \n\tCONSTRAINT fk_vaccinations_created_by_users FOREIGN KEY(created_by) REFERENCES users (id), \n\tCONSTRAINT fk_vaccinations_updated_by_users FOREIGN KEY(updated_by) REFERENCES users (id)\n)\n\n"
    )
    op.execute("CREATE INDEX ix_vaccinations_animal_id ON vaccinations (animal_id)")
    op.execute("CREATE INDEX ix_vaccinations_created_at ON vaccinations (created_at)")
    op.execute("CREATE INDEX ix_vaccinations_district ON vaccinations (district)")
    op.execute("CREATE INDEX ix_vaccinations_herd_id ON vaccinations (herd_id)")
    op.execute("CREATE INDEX ix_vaccinations_next_due_on ON vaccinations (next_due_on)")
    op.execute("CREATE INDEX ix_vaccinations_owner_id ON vaccinations (owner_id)")
    op.execute("CREATE INDEX ix_vaccinations_village ON vaccinations (village)")
    op.execute(
        "\nCREATE TABLE alerts (\n\ttype VARCHAR(40) NOT NULL, \n\tseverity VARCHAR(20) NOT NULL, \n\ttitle VARCHAR(200) NOT NULL, \n\tmessage TEXT NOT NULL, \n\tstate VARCHAR(100) NOT NULL, \n\tdistrict VARCHAR(100) NOT NULL, \n\tblock VARCHAR(100) NOT NULL, \n\tvillage VARCHAR(150) NOT NULL, \n\tuser_id UUID, \n\tcase_id UUID, \n\toutbreak_id UUID, \n\ttranslations JSONB NOT NULL, \n\tcreated_by UUID, \n\tid UUID NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tupdated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tCONSTRAINT pk_alerts PRIMARY KEY (id), \n\tCONSTRAINT fk_alerts_user_id_users FOREIGN KEY(user_id) REFERENCES users (id), \n\tCONSTRAINT fk_alerts_case_id_cases FOREIGN KEY(case_id) REFERENCES cases (id), \n\tCONSTRAINT fk_alerts_outbreak_id_outbreaks FOREIGN KEY(outbreak_id) REFERENCES outbreaks (id), \n\tCONSTRAINT fk_alerts_created_by_users FOREIGN KEY(created_by) REFERENCES users (id)\n)\n\n"
    )
    op.execute("CREATE INDEX ix_alerts_created_at ON alerts (created_at)")
    op.execute("CREATE INDEX ix_alerts_district ON alerts (district)")
    op.execute("CREATE INDEX ix_alerts_type ON alerts (type)")
    op.execute("CREATE INDEX ix_alerts_user_id ON alerts (user_id)")
    op.execute(
        "\nCREATE TABLE attachments (\n\tcase_id UUID NOT NULL, \n\tuploaded_by UUID NOT NULL, \n\tstorage_key VARCHAR(150) NOT NULL, \n\tcontent_type VARCHAR(80) NOT NULL, \n\tsize_bytes INTEGER NOT NULL, \n\tid UUID NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tupdated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tCONSTRAINT pk_attachments PRIMARY KEY (id), \n\tCONSTRAINT fk_attachments_case_id_cases FOREIGN KEY(case_id) REFERENCES cases (id), \n\tCONSTRAINT fk_attachments_uploaded_by_users FOREIGN KEY(uploaded_by) REFERENCES users (id), \n\tCONSTRAINT uq_attachments_storage_key UNIQUE (storage_key)\n)\n\n"
    )
    op.execute("CREATE INDEX ix_attachments_case_id ON attachments (case_id)")
    op.execute("CREATE INDEX ix_attachments_created_at ON attachments (created_at)")
    op.execute(
        "\nCREATE TABLE case_symptoms (\n\tcase_id UUID NOT NULL, \n\tsymptom_code VARCHAR(3) NOT NULL, \n\tsymptom_value INTEGER NOT NULL, \n\tid UUID NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tupdated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tCONSTRAINT pk_case_symptoms PRIMARY KEY (id), \n\tCONSTRAINT uq_case_symptoms_case_id UNIQUE (case_id, symptom_code), \n\tCONSTRAINT ck_case_symptoms_binary_value CHECK (symptom_value IN (0,1)), \n\tCONSTRAINT fk_case_symptoms_case_id_cases FOREIGN KEY(case_id) REFERENCES cases (id)\n)\n\n"
    )
    op.execute("CREATE INDEX ix_case_symptoms_case_id ON case_symptoms (case_id)")
    op.execute("CREATE INDEX ix_case_symptoms_created_at ON case_symptoms (created_at)")
    op.execute(
        "\nCREATE TABLE lab_referrals (\n\tsample_reference VARCHAR(40) NOT NULL, \n\tcase_id UUID NOT NULL, \n\tanimal_id UUID, \n\towner_id UUID NOT NULL, \n\tdistrict VARCHAR(100) NOT NULL, \n\trequested_by UUID NOT NULL, \n\tsample_type VARCHAR(150) NOT NULL, \n\tsuspected_disease VARCHAR(150), \n\tcollection_date DATE, \n\tlaboratory_name VARCHAR(200) NOT NULL, \n\tstatus VARCHAR(30) NOT NULL, \n\tresult TEXT, \n\tresult_date DATE, \n\tresult_key VARCHAR(100), \n\tnotes TEXT NOT NULL, \n\tid UUID NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tupdated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tcreated_by UUID, \n\tupdated_by UUID, \n\tCONSTRAINT pk_lab_referrals PRIMARY KEY (id), \n\tCONSTRAINT uq_lab_referrals_sample_reference UNIQUE (sample_reference), \n\tCONSTRAINT fk_lab_referrals_case_id_cases FOREIGN KEY(case_id) REFERENCES cases (id), \n\tCONSTRAINT fk_lab_referrals_animal_id_animals FOREIGN KEY(animal_id) REFERENCES animals (id), \n\tCONSTRAINT fk_lab_referrals_owner_id_users FOREIGN KEY(owner_id) REFERENCES users (id), \n\tCONSTRAINT fk_lab_referrals_requested_by_users FOREIGN KEY(requested_by) REFERENCES users (id), \n\tCONSTRAINT fk_lab_referrals_created_by_users FOREIGN KEY(created_by) REFERENCES users (id), \n\tCONSTRAINT fk_lab_referrals_updated_by_users FOREIGN KEY(updated_by) REFERENCES users (id)\n)\n\n"
    )
    op.execute("CREATE INDEX ix_lab_referrals_case_id ON lab_referrals (case_id)")
    op.execute("CREATE INDEX ix_lab_referrals_created_at ON lab_referrals (created_at)")
    op.execute("CREATE INDEX ix_lab_referrals_district ON lab_referrals (district)")
    op.execute("CREATE INDEX ix_lab_referrals_owner_id ON lab_referrals (owner_id)")
    op.execute("CREATE INDEX ix_lab_referrals_status ON lab_referrals (status)")
    op.execute(
        "\nCREATE TABLE outbreak_cases (\n\toutbreak_id UUID NOT NULL, \n\tcase_id UUID NOT NULL, \n\tid UUID NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tupdated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tCONSTRAINT pk_outbreak_cases PRIMARY KEY (id), \n\tCONSTRAINT uq_outbreak_cases_outbreak_id UNIQUE (outbreak_id, case_id), \n\tCONSTRAINT fk_outbreak_cases_outbreak_id_outbreaks FOREIGN KEY(outbreak_id) REFERENCES outbreaks (id), \n\tCONSTRAINT fk_outbreak_cases_case_id_cases FOREIGN KEY(case_id) REFERENCES cases (id)\n)\n\n"
    )
    op.execute("CREATE INDEX ix_outbreak_cases_case_id ON outbreak_cases (case_id)")
    op.execute("CREATE INDEX ix_outbreak_cases_created_at ON outbreak_cases (created_at)")
    op.execute("CREATE INDEX ix_outbreak_cases_outbreak_id ON outbreak_cases (outbreak_id)")
    op.execute(
        "\nCREATE TABLE predictions (\n\tcase_id UUID, \n\trequested_by UUID NOT NULL, \n\tmodel_name VARCHAR(100) NOT NULL, \n\tmodel_version VARCHAR(50) NOT NULL, \n\tinput_features JSONB NOT NULL, \n\tpredicted_class VARCHAR(150) NOT NULL, \n\tprobability FLOAT, \n\tid UUID NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tupdated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tCONSTRAINT pk_predictions PRIMARY KEY (id), \n\tCONSTRAINT fk_predictions_case_id_cases FOREIGN KEY(case_id) REFERENCES cases (id), \n\tCONSTRAINT fk_predictions_requested_by_users FOREIGN KEY(requested_by) REFERENCES users (id)\n)\n\n"
    )
    op.execute("CREATE INDEX ix_predictions_case_id ON predictions (case_id)")
    op.execute("CREATE INDEX ix_predictions_created_at ON predictions (created_at)")
    op.execute(
        "\nCREATE TABLE treatments (\n\tcase_id UUID NOT NULL, \n\tanimal_id UUID, \n\tveterinarian_id UUID NOT NULL, \n\towner_id UUID NOT NULL, \n\tdistrict VARCHAR(100) NOT NULL, \n\ttreatment_description TEXT NOT NULL, \n\tmedication VARCHAR(300), \n\tdosage VARCHAR(300), \n\tstarted_on DATE NOT NULL, \n\tended_on DATE, \n\tnotes TEXT NOT NULL, \n\tid UUID NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tupdated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tcreated_by UUID, \n\tupdated_by UUID, \n\tCONSTRAINT pk_treatments PRIMARY KEY (id), \n\tCONSTRAINT ck_treatments_ordered_dates CHECK (ended_on IS NULL OR ended_on >= started_on), \n\tCONSTRAINT fk_treatments_case_id_cases FOREIGN KEY(case_id) REFERENCES cases (id), \n\tCONSTRAINT fk_treatments_animal_id_animals FOREIGN KEY(animal_id) REFERENCES animals (id), \n\tCONSTRAINT fk_treatments_veterinarian_id_users FOREIGN KEY(veterinarian_id) REFERENCES users (id), \n\tCONSTRAINT fk_treatments_owner_id_users FOREIGN KEY(owner_id) REFERENCES users (id), \n\tCONSTRAINT fk_treatments_created_by_users FOREIGN KEY(created_by) REFERENCES users (id), \n\tCONSTRAINT fk_treatments_updated_by_users FOREIGN KEY(updated_by) REFERENCES users (id)\n)\n\n"
    )
    op.execute("CREATE INDEX ix_treatments_case_id ON treatments (case_id)")
    op.execute("CREATE INDEX ix_treatments_created_at ON treatments (created_at)")
    op.execute("CREATE INDEX ix_treatments_district ON treatments (district)")
    op.execute("CREATE INDEX ix_treatments_owner_id ON treatments (owner_id)")
    op.execute(
        "\nCREATE TABLE alert_reads (\n\talert_id UUID NOT NULL, \n\tuser_id UUID NOT NULL, \n\tis_read BOOLEAN NOT NULL, \n\tid UUID NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tupdated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tCONSTRAINT pk_alert_reads PRIMARY KEY (id), \n\tCONSTRAINT uq_alert_reads_alert_id UNIQUE (alert_id, user_id), \n\tCONSTRAINT fk_alert_reads_alert_id_alerts FOREIGN KEY(alert_id) REFERENCES alerts (id), \n\tCONSTRAINT fk_alert_reads_user_id_users FOREIGN KEY(user_id) REFERENCES users (id)\n)\n\n"
    )
    op.execute("CREATE INDEX ix_alert_reads_alert_id ON alert_reads (alert_id)")
    op.execute("CREATE INDEX ix_alert_reads_created_at ON alert_reads (created_at)")
    op.execute("CREATE INDEX ix_alert_reads_user_id ON alert_reads (user_id)")


def downgrade():
    op.drop_table("alert_reads")
    op.drop_table("treatments")
    op.drop_table("predictions")
    op.drop_table("outbreak_cases")
    op.drop_table("lab_referrals")
    op.drop_table("case_symptoms")
    op.drop_table("attachments")
    op.drop_table("alerts")
    op.drop_table("vaccinations")
    op.drop_table("cases")
    op.drop_table("animal_records")
    op.drop_table("outbreaks")
    op.drop_table("herds")
    op.drop_table("auth_sessions")
    op.drop_table("audit_logs")
    op.drop_table("animals")
    op.drop_table("users")
    op.drop_table("locations")
    op.drop_table("historical_observations")
