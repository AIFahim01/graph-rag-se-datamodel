#!/usr/bin/env python3

from orchestrator import DataPreprocessingOrchestrator

def main():
    input_folder = r'/home/user/Projects/office/data/GC 2025'
    output_folder = r'/home/user/Projects/office/data/Processed-data'

    print(f"=> Input folder: {input_folder}")
    print(f"=> Output folder: {output_folder}")

    orchestrator = DataPreprocessingOrchestrator(input_folder, output_folder)
    success = orchestrator.run()
    
    exit(0 if success else 1)

if __name__ == "__main__":
    main()
