<?php

namespace App\Command;


namespace App\Command;

use Psr\Log\LoggerInterface;
use Symfony\Component\Console\Command\Command;
use Symfony\Component\Console\Input\InputArgument;
use Symfony\Component\Console\Input\InputInterface;
use Symfony\Component\Console\Input\InputOption;
use Symfony\Component\Console\Logger\ConsoleLogger;
use Symfony\Component\Console\Output\OutputInterface;

class TestLogInterfaceCommand extends Command
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
            ->setName('app:test-log-interface')
            ->setDescription('Test log command')
            ->setHelp('This command allows you to test logging functionality...');
    }

    public function execute(InputInterface $input, OutputInterface $output): int
    {

        $output->writeln('---');
        $output->writeln('<info>Test log command output:</info>');
        $this->logger->info('Test log command started');
        $this->logger->info('This is an info message');
        $this->logger->error('This is an error message');
        $this->logger->warning('This is a warning message');
        $this->logger->debug('This is a debug message');
        $this->logger->notice('This is a notice message');
        $this->logger->critical('This is a critical message');
        $this->logger->alert('This is an alert message');
        $this->logger->emergency('This is an emergency message');
        $this->logger->info('Test log command finished');
        $output->writeln('---');

        return Command::SUCCESS;
    }
}