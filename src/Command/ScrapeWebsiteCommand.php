<?php

namespace App\Command;

use Symfony\Component\Console\Command\Command;
use Symfony\Component\Console\Input\InputArgument;
use Symfony\Component\Console\Input\InputInterface;
use Symfony\Component\Console\Input\InputOption;
use Symfony\Component\Console\Output\OutputInterface;
use Symfony\Component\BrowserKit\HttpBrowser;
use Symfony\Component\HttpClient\HttpClient;
use Symfony\Component\DomCrawler\Crawler;
use Symfony\Contracts\HttpClient\HttpClientInterface;


class ScrapeWebsiteCommand extends Command
{
    protected function configure()
    {
        $this
            ->setName('app:scrape-website')
            ->setDescription('Scrapes a website and returns the data.')
            ->setHelp('This command allows you to scrape a website and return the data...');
    }

    protected function execute(InputInterface $input, OutputInterface $output): int
    {
        $url =  'https://www.gamestop.com/consoles-hardware/nintendo-switch/consoles/products/nintendo-switch-2/424543.html';

        $browser = new HttpBrowser(HttpClient::create());

        $output->writeln("<info>Scraping Url: $url</info>");

        $output->writeln("<info>Opening Browser</info>");

        $browser->request('GET', $url);
        $crawler = new Crawler($browser->getResponse()->getContent());

        $crawler = $crawler->filter('div.product-name-section h2.product-name');
        dump($crawler);
        $output->write($crawler);

        return Command::SUCCESS;
    }
}