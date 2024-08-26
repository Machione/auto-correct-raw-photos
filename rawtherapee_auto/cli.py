import click
import time
import processing

@click.command()
@click.argument("input_directory", type=click.Path(exists=True, file_okay=False))
@click.argument("output_directory", type=click.Path(file_okay=False))
def main(input_directory, output_directory):
    p = processing.Processor(input_directory, output_directory)
    p.run()
    while p.done == False:
        time.sleep(0.1)


if __name__ == "__main__":
    main()