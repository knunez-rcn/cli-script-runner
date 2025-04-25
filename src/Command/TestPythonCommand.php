<?php

namespace App\Command;

use Psr\Log\LoggerInterface;
use Symfony\Component\Console\Command\Command;
use Symfony\Component\Console\Input\InputInterface;
use Symfony\Component\Console\Input\InputOption;
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
            ->addOption('save', null, InputOption::VALUE_NONE, 'Save the output to a file')
            ->setHelp('This command executes the Python script with various parameters and returns the outputs...');
    }

    protected function execute(InputInterface $input, OutputInterface $output): int
    {
//        $scriptPath = __DIR__ . '/../../remote_control_stb.py';
        $scriptPath = __DIR__ . '/../Domain/modifiedScripts/remote_control_stb.py';

        $saveToFile = $input->getOption('save');

        $timestamp = date('Y-m-d H:i:s');

//        $logFilePath = $saveToFile ? __DIR__ . "/../../var/log/python_script.log" : null;

        if (!file_exists($scriptPath)) {
            $this->logger->error('Script not found', ['path' => $scriptPath]);
            $output->writeln('<error>Script not found at: ' . $scriptPath . '</error>');
            return Command::FAILURE;
        }

        $output->writeln('---');
        $output->writeln('<info>Python script output:</info>');

        $process = new Process(['python3', $scriptPath]);
//        if (str_contains($scriptPath, 'Domain/modifiedScripts/')) {
//            $process = new Process(['python3', escapeshellarg($scriptPath)]);
//        }

        $output->writeln('<info>Python started:</info>');
        $this->logger->info('Python script started');
        for ($i = 1; $i <= 27; $i++) {
            $process->setInput($i . "\n");
            $process->setTimeout(60);
            $process->start();
            $process->wait(function ($type, $buffer) use ($output, $process, $i) {
                if (Process::OUT === $type) {
                    $output->write($buffer);
                    $this->logger->info("Running Command: $i", ['processOutput' => $process->getOutput()]);
                } else {
                    $output->write("<error>$buffer</error>");
                }
            });

            sleep(5);
        }


        return Command::SUCCESS;
    }

    private function saveOutput(string $output, string $filePath): void
    {
        $directory = dirname($filePath);
        if (!is_dir($directory)) {
            mkdir($directory, 0777, true);
        }

        file_put_contents($filePath, $output);
        $this->logger->info('Output saved to file', ['path' => $filePath]);
    }
}