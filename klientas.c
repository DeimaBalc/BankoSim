#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <sys/un.h>

#define SOKETO_FAILAS "./banko_sim.sock"
#define BUFERIO_DYDIS 4096

// Function to handle errors and print messages
void klaida(const char *pranesimas) {
    perror(pranesimas);
    exit(EXIT_FAILURE);
}

int main() {
    int soketas;
    struct sockaddr_un serverio_adresas;
    char buferis[BUFERIO_DYDIS];

    // Create a Unix domain socket
    if ((soketas = socket(AF_UNIX, SOCK_STREAM, 0)) < 0)
        klaida("Nepavyko sukurti soketo...");

    // Set up the server address structure
    memset(&serverio_adresas, 0, sizeof(serverio_adresas));
    memset(buferis, 0, BUFERIO_DYDIS);
    
    serverio_adresas.sun_family = AF_UNIX;
    strncpy(serverio_adresas.sun_path, SOKETO_FAILAS, sizeof(serverio_adresas.sun_path) - 1);

    // Connect to the server
    if (connect(soketas, (struct sockaddr *)&serverio_adresas, sizeof(serverio_adresas)) < 0)
        klaida("Nepavyko prisijungti prie serverio ...");

    printf("Prisijungta prie serverio.\n");

    // Receive initial message from the server
    memset(buferis, 0, BUFERIO_DYDIS);
    if (recv(soketas, buferis, BUFERIO_DYDIS, 0) > 0)
        printf("%s\n", buferis);

    // Communication loop
    while (1) {
        printf(":");
        fgets(buferis, BUFERIO_DYDIS, stdin);

        // Nuvalome \n
        buferis[strcspn(buferis, "\n")] = '\0';
        // Jeigu įvedėme "exit"
        if (strcmp(buferis, "exit") == 0)
            break;

        send(soketas, buferis, strlen(buferis), 0);
        memset(buferis, 0, BUFERIO_DYDIS);

        if (recv(soketas, buferis, BUFERIO_DYDIS, 0) > 0)
            printf("%s", buferis);
        if (strncmp("PABAIGA", buferis, 7) == 0) 
            break;   
    }

    // Close the socket
    close(soketas);
    printf("Seansas baigėsi.\n\n");

    return 0;
}