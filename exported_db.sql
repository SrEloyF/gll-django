CREATE TABLE `auth_group` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(150) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `auth_group_permissions` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `group_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  KEY `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `auth_permission` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `content_type_id` int(11) NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=49 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

INSERT INTO auth_permission VALUES (1, Can add color, 1, add_color);
INSERT INTO auth_permission VALUES (2, Can change color, 1, change_color);
INSERT INTO auth_permission VALUES (3, Can delete color, 1, delete_color);
INSERT INTO auth_permission VALUES (4, Can view color, 1, view_color);
INSERT INTO auth_permission VALUES (5, Can add dueno anterior, 2, add_duenoanterior);
INSERT INTO auth_permission VALUES (6, Can change dueno anterior, 2, change_duenoanterior);
INSERT INTO auth_permission VALUES (7, Can delete dueno anterior, 2, delete_duenoanterior);
INSERT INTO auth_permission VALUES (8, Can view dueno anterior, 2, view_duenoanterior);
INSERT INTO auth_permission VALUES (9, Can add estado, 3, add_estado);
INSERT INTO auth_permission VALUES (10, Can change estado, 3, change_estado);
INSERT INTO auth_permission VALUES (11, Can delete estado, 3, delete_estado);
INSERT INTO auth_permission VALUES (12, Can view estado, 3, view_estado);
INSERT INTO auth_permission VALUES (13, Can add galpon, 4, add_galpon);
INSERT INTO auth_permission VALUES (14, Can change galpon, 4, change_galpon);
INSERT INTO auth_permission VALUES (15, Can delete galpon, 4, delete_galpon);
INSERT INTO auth_permission VALUES (16, Can view galpon, 4, view_galpon);
INSERT INTO auth_permission VALUES (17, Can add gallo, 5, add_gallo);
INSERT INTO auth_permission VALUES (18, Can change gallo, 5, change_gallo);
INSERT INTO auth_permission VALUES (19, Can delete gallo, 5, delete_gallo);
INSERT INTO auth_permission VALUES (20, Can view gallo, 5, view_gallo);
INSERT INTO auth_permission VALUES (21, Can add encuentro, 6, add_encuentro);
INSERT INTO auth_permission VALUES (22, Can change encuentro, 6, change_encuentro);
INSERT INTO auth_permission VALUES (23, Can delete encuentro, 6, delete_encuentro);
INSERT INTO auth_permission VALUES (24, Can view encuentro, 6, view_encuentro);
INSERT INTO auth_permission VALUES (25, Can add log entry, 7, add_logentry);
INSERT INTO auth_permission VALUES (26, Can change log entry, 7, change_logentry);
INSERT INTO auth_permission VALUES (27, Can delete log entry, 7, delete_logentry);
INSERT INTO auth_permission VALUES (28, Can view log entry, 7, view_logentry);
INSERT INTO auth_permission VALUES (29, Can add permission, 8, add_permission);
INSERT INTO auth_permission VALUES (30, Can change permission, 8, change_permission);
INSERT INTO auth_permission VALUES (31, Can delete permission, 8, delete_permission);
INSERT INTO auth_permission VALUES (32, Can view permission, 8, view_permission);
INSERT INTO auth_permission VALUES (33, Can add group, 9, add_group);
INSERT INTO auth_permission VALUES (34, Can change group, 9, change_group);
INSERT INTO auth_permission VALUES (35, Can delete group, 9, delete_group);
INSERT INTO auth_permission VALUES (36, Can view group, 9, view_group);
INSERT INTO auth_permission VALUES (37, Can add user, 10, add_user);
INSERT INTO auth_permission VALUES (38, Can change user, 10, change_user);
INSERT INTO auth_permission VALUES (39, Can delete user, 10, delete_user);
INSERT INTO auth_permission VALUES (40, Can view user, 10, view_user);
INSERT INTO auth_permission VALUES (41, Can add content type, 11, add_contenttype);
INSERT INTO auth_permission VALUES (42, Can change content type, 11, change_contenttype);
INSERT INTO auth_permission VALUES (43, Can delete content type, 11, delete_contenttype);
INSERT INTO auth_permission VALUES (44, Can view content type, 11, view_contenttype);
INSERT INTO auth_permission VALUES (45, Can add session, 12, add_session);
INSERT INTO auth_permission VALUES (46, Can change session, 12, change_session);
INSERT INTO auth_permission VALUES (47, Can delete session, 12, delete_session);
INSERT INTO auth_permission VALUES (48, Can view session, 12, view_session);
CREATE TABLE `auth_user` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `password` varchar(128) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) NOT NULL,
  `first_name` varchar(150) NOT NULL,
  `last_name` varchar(150) NOT NULL,
  `email` varchar(254) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `auth_user_groups` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `group_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_groups_user_id_group_id_94350c0c_uniq` (`user_id`,`group_id`),
  KEY `auth_user_groups_group_id_97559544_fk_auth_group_id` (`group_id`),
  CONSTRAINT `auth_user_groups_group_id_97559544_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  CONSTRAINT `auth_user_groups_user_id_6a12ed8b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `auth_user_user_permissions` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_user_permissions_user_id_permission_id_14a6b632_uniq` (`user_id`,`permission_id`),
  KEY `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `django_admin_log` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext DEFAULT NULL,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint(5) unsigned NOT NULL CHECK (`action_flag` >= 0),
  `change_message` longtext NOT NULL,
  `content_type_id` int(11) DEFAULT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  KEY `django_admin_log_user_id_c564eba6_fk_auth_user_id` (`user_id`),
  CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `django_admin_log_user_id_c564eba6_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `django_content_type` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

INSERT INTO django_content_type VALUES (7, admin, logentry);
INSERT INTO django_content_type VALUES (9, auth, group);
INSERT INTO django_content_type VALUES (8, auth, permission);
INSERT INTO django_content_type VALUES (10, auth, user);
INSERT INTO django_content_type VALUES (11, contenttypes, contenttype);
INSERT INTO django_content_type VALUES (1, gll_app, color);
INSERT INTO django_content_type VALUES (2, gll_app, duenoanterior);
INSERT INTO django_content_type VALUES (6, gll_app, encuentro);
INSERT INTO django_content_type VALUES (3, gll_app, estado);
INSERT INTO django_content_type VALUES (5, gll_app, gallo);
INSERT INTO django_content_type VALUES (4, gll_app, galpon);
INSERT INTO django_content_type VALUES (12, sessions, session);
CREATE TABLE `django_migrations` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `app` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=20 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

INSERT INTO django_migrations VALUES (1, contenttypes, 0001_initial, 2025-06-01 01:26:06.298149);
INSERT INTO django_migrations VALUES (2, auth, 0001_initial, 2025-06-01 01:26:06.522141);
INSERT INTO django_migrations VALUES (3, admin, 0001_initial, 2025-06-01 01:26:06.568682);
INSERT INTO django_migrations VALUES (4, admin, 0002_logentry_remove_auto_add, 2025-06-01 01:26:06.573694);
INSERT INTO django_migrations VALUES (5, admin, 0003_logentry_add_action_flag_choices, 2025-06-01 01:26:06.579680);
INSERT INTO django_migrations VALUES (6, contenttypes, 0002_remove_content_type_name, 2025-06-01 01:26:06.631975);
INSERT INTO django_migrations VALUES (7, auth, 0002_alter_permission_name_max_length, 2025-06-01 01:26:06.672227);
INSERT INTO django_migrations VALUES (8, auth, 0003_alter_user_email_max_length, 2025-06-01 01:26:06.690690);
INSERT INTO django_migrations VALUES (9, auth, 0004_alter_user_username_opts, 2025-06-01 01:26:06.696777);
INSERT INTO django_migrations VALUES (10, auth, 0005_alter_user_last_login_null, 2025-06-01 01:26:06.728891);
INSERT INTO django_migrations VALUES (11, auth, 0006_require_contenttypes_0002, 2025-06-01 01:26:06.730882);
INSERT INTO django_migrations VALUES (12, auth, 0007_alter_validators_add_error_messages, 2025-06-01 01:26:06.736495);
INSERT INTO django_migrations VALUES (13, auth, 0008_alter_user_username_max_length, 2025-06-01 01:26:06.754004);
INSERT INTO django_migrations VALUES (14, auth, 0009_alter_user_last_name_max_length, 2025-06-01 01:26:06.770230);
INSERT INTO django_migrations VALUES (15, auth, 0010_alter_group_name_max_length, 2025-06-01 01:26:06.785982);
INSERT INTO django_migrations VALUES (16, auth, 0011_update_proxy_permissions, 2025-06-01 01:26:06.785982);
INSERT INTO django_migrations VALUES (17, auth, 0012_alter_user_first_name_max_length, 2025-06-01 01:26:06.808258);
INSERT INTO django_migrations VALUES (18, gll_app, 0001_initial, 2025-06-01 01:26:07.029242);
INSERT INTO django_migrations VALUES (19, sessions, 0001_initial, 2025-06-01 01:26:07.052616);
CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `gll_app_color` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `nombre` (`nombre`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

INSERT INTO gll_app_color VALUES (2, BLANCO);
INSERT INTO gll_app_color VALUES (3, MARRÓN);
INSERT INTO gll_app_color VALUES (1, NEGRO);
CREATE TABLE `gll_app_duenoanterior` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `nombre` (`nombre`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

INSERT INTO gll_app_duenoanterior VALUES (1, ABNER);
INSERT INTO gll_app_duenoanterior VALUES (2, JUANCITO);
INSERT INTO gll_app_duenoanterior VALUES (3, PABLO);
INSERT INTO gll_app_duenoanterior VALUES (4, PURI);
CREATE TABLE `gll_app_encuentro` (
  `idEncuentro` int(11) NOT NULL AUTO_INCREMENT,
  `fechaYHora` datetime(6) NOT NULL,
  `resultado` varchar(20) NOT NULL,
  `video` varchar(100) DEFAULT NULL,
  `imagen_evento` varchar(100) DEFAULT NULL,
  `pactada` decimal(10,2) NOT NULL,
  `pago_juez` decimal(10,2) DEFAULT NULL,
  `apuesta_general` decimal(10,2) NOT NULL,
  `premio_mayor` decimal(10,2) NOT NULL,
  `porcentaje_premio_mayor` decimal(5,2) NOT NULL,
  `apuesta_por_fuera` decimal(10,2) NOT NULL,
  `condicionGallo_id` bigint(20) NOT NULL,
  `gallo_id` int(11) NOT NULL,
  `galpon1_id` bigint(20) NOT NULL,
  `galpon2_id` bigint(20) NOT NULL,
  PRIMARY KEY (`idEncuentro`),
  KEY `gll_app_encuentro_condicionGallo_id_efc4f5fa_fk_gll_app_e` (`condicionGallo_id`),
  KEY `gll_app_encuentro_gallo_id_00a63d9f_fk_gll_app_gallo_idGallo` (`gallo_id`),
  KEY `gll_app_encuentro_galpon1_id_9c1be6ff_fk_gll_app_galpon_id` (`galpon1_id`),
  KEY `gll_app_encuentro_galpon2_id_2fa016a1_fk_gll_app_galpon_id` (`galpon2_id`),
  CONSTRAINT `gll_app_encuentro_condicionGallo_id_efc4f5fa_fk_gll_app_e` FOREIGN KEY (`condicionGallo_id`) REFERENCES `gll_app_estado` (`id`),
  CONSTRAINT `gll_app_encuentro_gallo_id_00a63d9f_fk_gll_app_gallo_idGallo` FOREIGN KEY (`gallo_id`) REFERENCES `gll_app_gallo` (`idGallo`),
  CONSTRAINT `gll_app_encuentro_galpon1_id_9c1be6ff_fk_gll_app_galpon_id` FOREIGN KEY (`galpon1_id`) REFERENCES `gll_app_galpon` (`id`),
  CONSTRAINT `gll_app_encuentro_galpon2_id_2fa016a1_fk_gll_app_galpon_id` FOREIGN KEY (`galpon2_id`) REFERENCES `gll_app_galpon` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

INSERT INTO gll_app_encuentro VALUES (1, 2025-06-03 13:01:00, V, , , 100.00, 50.00, 2000.00, 5000.00, 10.00, 800.00, 1, 2, 1, 1);
CREATE TABLE `gll_app_estado` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `nombre` (`nombre`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

INSERT INTO gll_app_estado VALUES (2, BISOJO);
INSERT INTO gll_app_estado VALUES (1, SANO);
INSERT INTO gll_app_estado VALUES (3, TONTO XD);
CREATE TABLE `gll_app_gallo` (
  `idGallo` int(11) NOT NULL AUTO_INCREMENT,
  `nroPlaca` int(11) DEFAULT NULL,
  `fechaNac` date NOT NULL,
  `sexo` varchar(1) NOT NULL,
  `tipoGallo` varchar(20) NOT NULL,
  `peso` decimal(10,2) NOT NULL,
  `nroPlacaAnterior` int(11) DEFAULT NULL,
  `fechaMuerte` date DEFAULT NULL,
  `observaciones` longtext NOT NULL,
  `nombre_img` varchar(100) NOT NULL,
  `color_id` bigint(20) NOT NULL,
  `estadoDeSalud_id` bigint(20) NOT NULL,
  `nombreDuenoAnterior_id` bigint(20) DEFAULT NULL,
  `placaMadre_id` int(11) DEFAULT NULL,
  `placaPadre_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`idGallo`),
  UNIQUE KEY `nroPlaca` (`nroPlaca`),
  KEY `gll_app_gallo_color_id_86b5b00b_fk_gll_app_color_id` (`color_id`),
  KEY `gll_app_gallo_estadoDeSalud_id_e197f5c6_fk_gll_app_estado_id` (`estadoDeSalud_id`),
  KEY `gll_app_gallo_nombreDuenoAnterior__e4f041b8_fk_gll_app_d` (`nombreDuenoAnterior_id`),
  KEY `gll_app_gallo_placaMadre_id_83eff4d5_fk_gll_app_gallo_idGallo` (`placaMadre_id`),
  KEY `gll_app_gallo_placaPadre_id_6827f07e_fk_gll_app_gallo_idGallo` (`placaPadre_id`),
  CONSTRAINT `gll_app_gallo_color_id_86b5b00b_fk_gll_app_color_id` FOREIGN KEY (`color_id`) REFERENCES `gll_app_color` (`id`),
  CONSTRAINT `gll_app_gallo_estadoDeSalud_id_e197f5c6_fk_gll_app_estado_id` FOREIGN KEY (`estadoDeSalud_id`) REFERENCES `gll_app_estado` (`id`),
  CONSTRAINT `gll_app_gallo_nombreDuenoAnterior__e4f041b8_fk_gll_app_d` FOREIGN KEY (`nombreDuenoAnterior_id`) REFERENCES `gll_app_duenoanterior` (`id`),
  CONSTRAINT `gll_app_gallo_placaMadre_id_83eff4d5_fk_gll_app_gallo_idGallo` FOREIGN KEY (`placaMadre_id`) REFERENCES `gll_app_gallo` (`idGallo`),
  CONSTRAINT `gll_app_gallo_placaPadre_id_6827f07e_fk_gll_app_gallo_idGallo` FOREIGN KEY (`placaPadre_id`) REFERENCES `gll_app_gallo` (`idGallo`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

INSERT INTO gll_app_gallo VALUES (1, 103, 2025-01-30, M, DP, 5.00, None, None, NINGUNA POR AHORA, gallos/1748966419.jpg, 1, 1, None, None, None);
INSERT INTO gll_app_gallo VALUES (2, 104, 2025-01-30, H, MADRE, 6.00, None, None, ES BONITA, XDD, gallos/1748971407.jpg, 2, 1, None, None, None);
INSERT INTO gll_app_gallo VALUES (3, 105, 2025-01-30, H, PADRE, 3.00, 100, None, NINGUNA POR AHORA, gallos/1749093354.jpeg, 3, 2, 2, None, None);
INSERT INTO gll_app_gallo VALUES (4, 106, 2020-01-30, M, PADRE, 7.00, None, None, NINGUNA, gallos/1749093460.jpeg, 2, 1, 3, None, None);
INSERT INTO gll_app_gallo VALUES (5, 107, 2023-01-30, H, MADRE, 7.00, None, None, NINGUNA, gallos/1749093820.jpg, 3, 3, None, 3, 1);
INSERT INTO gll_app_gallo VALUES (6, 108, 2006-10-19, M, MADRE, 9.00, None, None, MEH, gallos/1749094081.jpg, 2, 1, None, None, None);
CREATE TABLE `gll_app_galpon` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) NOT NULL,
  `dueno` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `nombre` (`nombre`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

INSERT INTO gll_app_galpon VALUES (1, GALPÓN 1, ELOY);
INSERT INTO gll_app_galpon VALUES (2, GALPÓN 2, VILLANUEVA);
