<?php

namespace App\Command;

use Symfony\Component\Console\Command\Command;
use Symfony\Component\Console\Input\InputArgument;
use Symfony\Component\Console\Input\InputInterface;
use Symfony\Component\Console\Input\InputOption;
use Symfony\Component\Console\Logger\ConsoleLogger;
use Symfony\Component\Console\Output\OutputInterface;
class TestLogCommand extends Command
{
    protected function configure(): void
    {
        $this
            ->setName('app:test-log')
            ->setDescription('Test log command')
            ->setHelp('This command allows you to test logging functionality...');
    }
    public function execute(InputInterface $input, OutputInterface $output): int
    {
        $logger = new ConsoleLogger($output);

        $output->writeln('---');
        $output->writeln('<info>Test log command output:</info>');
        $logger->info('Test log command started');
        $logger->info('This is an info message');
        $logger->error('This is an error message');
        $logger->warning('This is a warning message');
        $logger->debug('This is a debug message');
        $logger->notice('This is a notice message');
        $logger->critical('This is a critical message');
        $logger->alert('This is an alert message');
        $logger->emergency('This is an emergency message');
        $logger->info('Test log command finished');
        $output->writeln('---');

        return Command::SUCCESS;
    }
}