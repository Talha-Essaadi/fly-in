import sys
from parser import MapParser, ParserError
from simulation import Simulation



def main():
    try:
        if len(sys.argv) != 2:
            print("Usage: python main.py <map_file>")
            sys.exit(1)
        file_path = sys.argv[1]
        parser = MapParser()

        map_data = parser.parse(file_path)
        simulation = Simulation(map_data)
        # print(map_data.zones)
        simulation.run()

    except ParserError as e:
        print(f"Parser error: {e}")
        sys.exit(1)
    # except Exception as e:
    #     print(f"Error: {e}")
    #     sys.exit(1)


if __name__ == "__main__":
    main()
