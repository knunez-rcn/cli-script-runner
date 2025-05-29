<?php

namespace App\Command;

use Psr\Log\LoggerInterface;
use Symfony\Component\Console\Command\Command;
use Symfony\Component\Console\Input\InputArgument;
use Symfony\Component\Console\Input\InputInterface;
use Symfony\Component\Console\Output\OutputInterface;
use Symfony\Component\Process\Process;

class TestPythonCommand extends Command
{
    private LoggerInterface $logger;

    public function __construct(LoggerInterface $logger)
    {
        parent::__construct();
        $this->logger = $logger;
    }

    protected function configure(): void
    {
        $this
            ->setName('app:test-inverto')
            ->setDescription('Runs a Python script to test the .NET application implementation.')
            ->setHelp('This command executes the Python script with various parameters and returns the outputs...')
            ->addArgument('commandsNum', InputArgument::OPTIONAL, 'The number of Python commands to execute');
    }

    protected function execute(InputInterface $input, OutputInterface $output): int
    {
//        $scriptPath = __DIR__ . '/../../remote_control_stb.py';
//        $scriptPath = __DIR__ . '/../Domain/Python/ModifiedScripts/remote_control_stb_04252025.py';
        $scriptPath = __DIR__ . '/../Domain/Python/ModifiedScripts/3path_remote_control_stb_20250504.py';

        if (!file_exists($scriptPath)) {
            $this->logger->error('Script not found', ['path' => $scriptPath]);
            $output->writeln('<error>Script not found at: ' . $scriptPath . '</error>');
            return Command::FAILURE;
        }

        $pythonCommandsCount = $input->getArgument('commandsNum') ?? 1;

        $output->writeln('---');

        $process = new Process(['python3', $scriptPath]);

        $output->writeln('<info>Python started:</info>');

        $this->logger->info('Python script started');

        for ($i = 1; $i <= $pythonCommandsCount; $i++) {
            $process->setInput($i . "\n");

            $process->setTimeout(60);

            $process->start();

            $process->wait(function ($type, $buffer) use ($output, $process, $i) {
                if (Process::OUT === $type) {
                    $fullOutput = $process->getOutput();

                    $parts = explode("====", $fullOutput);

                    $extractedContent = '';

                    if (isset($parts[1])) {
                        $extractedContent = trim($parts[1]);
                    }

                    $output->writeln($extractedContent);

                    $this->logger->info("Running Command: $i", ['processOutput' => $extractedContent]);

                    $output->writeln('----');
                } else {
                    $output->write("<error>$buffer</error>");
                }
            });

            sleep(5);
        }

        $output->writeln('---');
        return Command::SUCCESS;
    }
}