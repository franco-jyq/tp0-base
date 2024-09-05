import sys


FILENAME = sys.argv[1]
NUM_CLIENTS = sys.argv[2]


# Define the static part of the docker-compose file
docker_compose_template = """
version: '3'
name: tp0
services:
  server:
    container_name: server
    image: server:latest
    entrypoint: python3 /main.py
    environment:
      - PYTHONUNBUFFERED=1
    networks:
      - testing_net
    volumes:
      - ./server/config.ini:/config.ini
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




