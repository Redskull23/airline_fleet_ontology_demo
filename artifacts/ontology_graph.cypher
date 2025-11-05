CREATE CONSTRAINT IF NOT EXISTS FOR (n:Aircraft) REQUIRE n.aircraft_id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (n:Flight) REQUIRE n.flight_id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (n:SensorReading) REQUIRE n.reading_id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (n:WorkOrder) REQUIRE n.wo_id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (n:Part) REQUIRE n.part_number IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (n:Alert) REQUIRE n.alert_id IS UNIQUE;
// Relationships
MATCH (a:Aircraft), (b:SensorReading)
WHERE a.aircraft_id = b.aircraft_id
MERGE (a)-[:HAS_TELEMETRY]->(b);
MATCH (a:Aircraft), (b:WorkOrder)
WHERE a.aircraft_id = b.aircraft_id
MERGE (a)-[:HAS_MAINTENANCE_ACTION]->(b);
MATCH (a:WorkOrder), (b:Part)
WHERE a.part_number = b.part_number
MERGE (a)-[:CONSUMES_COMPONENT]->(b);
MATCH (a:Aircraft), (b:Alert)
WHERE a.aircraft_id = b.aircraft_id
MERGE (a)-[:HAS_HEALTH_SIGNAL]->(b);