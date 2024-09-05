import sys


FILENAME = sys.argv[1]
NUM_CLIENTS = sys.argv[2]


# Check if the number is a valid positive integer
if not NUM_CLIENTS.isdigit() or int(NUM_CLIENTS) <= 0:
    print("Error: NUM_CLIENTS must be a positive integer.", file=sys.stderr)
    sys.exit(1)


# Define the static part of the docker-compose file
docker_compose_template = """
version: '3'
services:
  server:
    container_name: server
    image: server:latest
    entrypoint: python3 /main.py
    environment:
      - PYTHONUNBUFFERED=1
      - LOGGING_LEVEL=INFO
    networks:
      - testing_net
    volumes:
      - ./server/config.ini:/config.ini
      - ./server/common/bets.csv:/bets.csv
"""

# Generate the client services dynamically
for i in range(1, int(NUM_CLIENTS) + 1):
    client_config = f"""
  client{i}:
    container_name: client{i}
    image: client:latest
    entrypoint: /client
    environment:
      - CLI_ID={i}
      - CLI_LOG_LEVEL=INFO
      - CLI_NOMBRE=Santiago Lionel
      - CLI_APELLIDO=Lorca
      - CLI_DOCUMENTO=30904465
      - CLI_NACIMIENTO=1999-03-17
      - CLI_NUMERO=7574
      - CLI_AGENCY_DATA_FILE=/data/agency-{i}.csv
    networks:
      - testing_net
    depends_on:
      - server
    volumes:
      - ./client/config.yaml:/config.yaml
    """
    docker_compose_template += client_config

# Add the networks section
docker_compose_template += """
networks:
  testing_net:
    name: testing_net
    ipam:
      driver: default
      config:
        - subnet: 172.25.125.0/24
"""

# Write the content in the file
try:
    with open(FILENAME, 'w') as file:
        file.write(docker_compose_template)
        print(f"{FILENAME} generated successfully with {NUM_CLIENTS} clients.")
except OSError as e:
    print(f"Error: Could not write to file. Reason: {e}", file=sys.stderr)
    sys.exit(1)




