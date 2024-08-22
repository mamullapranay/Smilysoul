-- MySQL dump 10.13  Distrib 8.0.23, for Win64 (x86_64)
--
-- Host: localhost    Database: maindb
-- ------------------------------------------------------
-- Server version	8.0.19

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `day_availability`
--

DROP TABLE IF EXISTS `day_availability`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `day_availability` (
  `counsellor_id` varchar(50) NOT NULL,
  `day_available` varchar(20) NOT NULL,
  `time_slot` time NOT NULL,
  `flag` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`counsellor_id`,`day_available`,`time_slot`),
  CONSTRAINT `day_availability_ibfk_1` FOREIGN KEY (`counsellor_id`) REFERENCES `counsellor` (`counsellor_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `day_availability`
--

LOCK TABLES `day_availability` WRITE;
/*!40000 ALTER TABLE `day_availability` DISABLE KEYS */;
INSERT INTO `day_availability` VALUES ('1','Friday','10:30:00',0),('1','Friday','11:15:00',0),('1','Friday','14:00:00',0),('1','Friday','14:45:00',0),('1','Monday','10:30:00',0),('1','Monday','11:15:00',1),('1','Monday','15:00:00',0),('1','Monday','15:45:00',0),('1','Saturday','01:00:00',0),('1','Sunday','12:15:00',0),('1','Thursday','10:30:00',0),('1','Thursday','11:15:00',0),('1','Thursday','14:00:00',0),('1','Tuesday','10:30:00',0),('1','Tuesday','11:15:00',0),('1','Wednesday','11:30:00',0),('1','Wednesday','12:15:00',0),('1','Wednesday','15:00:00',0),('1','Wednesday','15:45:00',0),('2','Friday','11:30:00',0),('2','Friday','12:15:00',0),('2','Friday','15:00:00',0),('2','Monday','11:30:00',1),('2','Monday','14:00:00',0),('2','Saturday','16:00:00',0),('2','Sunday','12:30:00',0),('2','Thursday','11:30:00',0),('2','Thursday','12:15:00',0),('2','Thursday','14:00:00',0),('2','Thursday','14:45:00',0),('2','Tuesday','11:30:00',0),('2','Tuesday','12:15:00',0),('2','Tuesday','15:15:00',0),('2','Wednesday','10:30:00',0),('2','Wednesday','11:15:00',0),('2','Wednesday','14:00:00',0),('2','Wednesday','14:45:00',0);
/*!40000 ALTER TABLE `day_availability` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2021-05-09 11:48:39
